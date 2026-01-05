#!/usr/bin/env python3
"""
3DGS Viewer Monitor - Daily Scanner

Searches GitHub for new 3D Gaussian Splatting viewer projects and uses
Claude to filter for interesting interactive viewers.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic


# Configuration
GITHUB_API_URL = "https://api.github.com"
SEARCH_QUERIES = [
    "gaussian splatting",
    "3dgs",
    "gsplat viewer",
    "splat viewer",
    "3d gaussian splat",
    "gaussian splat viewer",
]


def get_github_headers():
    """Get headers for GitHub API requests."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def search_github_repos(query: str, created_after: str) -> list:
    """
    Search GitHub for repos matching query created after a date.

    Args:
        query: Search query string
        created_after: ISO date string (YYYY-MM-DD)

    Returns:
        List of repo dictionaries
    """
    headers = get_github_headers()

    # Build search query with date filter, excluding forks
    search_query = f"{query} created:>{created_after} fork:false"

    params = {
        "q": search_query,
        "sort": "created",
        "order": "desc",
        "per_page": 100,
    }

    try:
        response = requests.get(
            f"{GITHUB_API_URL}/search/repositories",
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"Error searching GitHub for '{query}': {e}")
        return []


def deduplicate_repos(repos: list) -> list:
    """Remove duplicate repos based on full_name."""
    seen = set()
    unique = []
    for repo in repos:
        full_name = repo.get("full_name", "")
        if full_name and full_name not in seen:
            seen.add(full_name)
            unique.append(repo)
    return unique


def format_repo_for_analysis(repo: dict) -> dict:
    """Extract relevant fields from a repo for analysis."""
    return {
        "name": repo.get("full_name", "Unknown"),
        "description": repo.get("description", "No description"),
        "url": repo.get("html_url", ""),
        "stars": repo.get("stargazers_count", 0),
        "language": repo.get("language", "Unknown"),
        "created_at": repo.get("created_at", ""),
        "topics": repo.get("topics", []),
    }


def analyze_with_claude(repos: list) -> str:
    """
    Use Claude to analyze repos and identify interesting viewers.

    Args:
        repos: List of formatted repo dictionaries

    Returns:
        Claude's analysis as markdown string
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    if not repos:
        return "No new repositories found in the last 24 hours."

    # Format repos for the prompt
    repo_list = "\n".join([
        f"- **{r['name']}** ({r['language']}, {r['stars']} stars)\n"
        f"  Description: {r['description']}\n"
        f"  URL: {r['url']}\n"
        f"  Topics: {', '.join(r['topics']) if r['topics'] else 'None'}"
        for r in repos
    ])

    prompt = f"""Here are GitHub repos found in the last 24 hours related to 3D Gaussian Splatting:

{repo_list}

Which of these appear to be INTERACTIVE VIEWERS or creative presentation tools (web-based, with UI, playable experiences)?

Exclude:
- Training/research code (CUDA kernels, model training scripts)
- Raw data/datasets
- Python-only tools with no viewer component
- Forks of existing projects (should already be filtered out)
- Academic paper implementations without viewer
- Purely backend/API projects

For each interesting viewer project, provide:
1. The repo name and URL
2. What makes it interesting (unique features, novel approach, etc.)
3. Technology stack if discernible

If none of the repos appear to be interactive viewers, say so clearly.

Format your response as markdown suitable for a daily report."""

    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error analyzing with Claude: {e}"


def generate_daily_report(repos: list, analysis: str, date_str: str) -> str:
    """
    Generate the daily markdown report.

    Args:
        repos: List of all repos found
        analysis: Claude's analysis
        date_str: Date string for the report

    Returns:
        Complete markdown report
    """
    report = f"""# 3DGS Viewer Monitor - {date_str}

## Summary

- **Repos scanned**: {len(repos)}
- **Search queries**: {', '.join(SEARCH_QUERIES)}
- **Time range**: Last 24 hours

## Claude's Analysis

{analysis}

## All Repos Found

"""

    if repos:
        for repo in repos:
            report += f"""### [{repo['name']}]({repo['url']})

- **Language**: {repo['language']}
- **Stars**: {repo['stars']}
- **Created**: {repo['created_at'][:10] if repo['created_at'] else 'Unknown'}
- **Topics**: {', '.join(repo['topics']) if repo['topics'] else 'None'}
- **Description**: {repo['description']}

"""
    else:
        report += "*No new repos found in the last 24 hours.*\n"

    report += f"""
---
*Generated at {datetime.utcnow().isoformat()}Z by 3DGS Viewer Monitor*
"""

    return report


def save_report(report: str, date_str: str, findings_dir: Path) -> Path:
    """
    Save the report to the findings directory.

    Args:
        report: Markdown report content
        date_str: Date string for filename
        findings_dir: Path to findings directory

    Returns:
        Path to saved file
    """
    findings_dir.mkdir(parents=True, exist_ok=True)
    filepath = findings_dir / f"{date_str}.md"
    filepath.write_text(report)
    return filepath


def main():
    """Main entry point for the scanner."""
    print("Starting 3DGS Viewer Monitor scan...")

    # Calculate date range (last 24 hours)
    now = datetime.utcnow()
    yesterday = now - timedelta(days=1)
    created_after = yesterday.strftime("%Y-%m-%d")
    date_str = now.strftime("%Y-%m-%d")

    print(f"Searching for repos created after {created_after}")

    # Search for repos across all queries
    all_repos = []
    for query in SEARCH_QUERIES:
        print(f"Searching: '{query}'...")
        repos = search_github_repos(query, created_after)
        print(f"  Found {len(repos)} repos")
        all_repos.extend(repos)

    # Deduplicate
    unique_repos = deduplicate_repos(all_repos)
    print(f"Total unique repos found: {len(unique_repos)}")

    # Format for analysis
    formatted_repos = [format_repo_for_analysis(r) for r in unique_repos]

    # Analyze with Claude
    print("Analyzing with Claude...")
    analysis = analyze_with_claude(formatted_repos)

    # Generate report
    report = generate_daily_report(formatted_repos, analysis, date_str)

    # Save to findings directory
    script_dir = Path(__file__).parent
    findings_dir = script_dir / "findings"
    filepath = save_report(report, date_str, findings_dir)
    print(f"Report saved to: {filepath}")

    # Also save to a file that GitHub Actions can use for issue creation
    issue_file = script_dir / "latest_report.md"
    issue_file.write_text(report)
    print(f"Issue file saved to: {issue_file}")

    # Print summary
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print("=" * 60)
    print(f"Date: {date_str}")
    print(f"Repos found: {len(unique_repos)}")
    print(f"Report: {filepath}")

    return 0


if __name__ == "__main__":
    exit(main())
