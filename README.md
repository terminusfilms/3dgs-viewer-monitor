# 3DGS Viewer Monitor

A GitHub Action that runs daily to discover new 3D Gaussian Splatting viewer projects.

## What It Does

1. **Searches GitHub** for new repositories related to 3D Gaussian Splatting (created in the last 24 hours)
2. **Filters with Claude AI** to identify interactive viewers (not just training code or datasets)
3. **Creates a daily report** saved to `findings/YYYY-MM-DD.md`
4. **Opens a GitHub Issue** with the daily summary for easy browsing

## Search Queries

The scanner searches for repos matching:
- `gaussian splatting`
- `3dgs`
- `gsplat viewer`
- `splat viewer`
- `3d gaussian splat`
- `gaussian splat viewer`

Forks are automatically excluded.

## Setup

### 1. Create GitHub Repository

Push this code to a new GitHub repository.

### 2. Add Repository Secrets

Go to your repo's **Settings** > **Secrets and variables** > **Actions** and add:

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude |

Note: `GITHUB_TOKEN` is automatically provided by GitHub Actions.

### 3. Enable GitHub Actions

Actions should be enabled by default. The workflow will:
- Run automatically at **8:00 AM EST** (13:00 UTC) daily
- Can be triggered manually via the Actions tab

## Manual Run

To run the scanner manually:

1. Go to **Actions** tab in your repository
2. Select **Daily 3DGS Viewer Scan** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

## Local Development

### Prerequisites

- Python 3.11+
- GitHub personal access token
- Anthropic API key

### Installation

```bash
pip install -r requirements.txt
```

### Running Locally

```bash
export GITHUB_TOKEN="your_github_token"
export ANTHROPIC_API_KEY="your_anthropic_key"
python scan.py
```

### Getting a GitHub Token

1. Go to GitHub **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**
2. Generate new token with `public_repo` scope
3. Use this for local development

## Output

### Findings Directory

Daily reports are saved to `findings/YYYY-MM-DD.md` with:
- Summary statistics
- Claude's analysis of interesting viewers
- Full list of all repos found

### GitHub Issues

Each run creates a GitHub Issue labeled `daily-scan` and `automated` containing the same report, making it easy to browse historical scans.

## Project Structure

```
3dgs-viewer-monitor/
├── .github/
│   └── workflows/
│       └── daily-scan.yml    # GitHub Actions workflow
├── findings/                  # Daily report files
│   └── YYYY-MM-DD.md
├── scan.py                    # Main scanner script
├── requirements.txt           # Python dependencies
├── .gitignore
└── README.md
```

## Customization

### Change Schedule

Edit `.github/workflows/daily-scan.yml` and modify the cron expression:

```yaml
schedule:
  - cron: '0 13 * * *'  # Currently 8am EST / 1pm UTC
```

### Add Search Terms

Edit `SEARCH_QUERIES` in `scan.py`:

```python
SEARCH_QUERIES = [
    "gaussian splatting",
    "3dgs",
    # Add more queries here
]
```

### Modify Claude's Filtering

Edit the prompt in the `analyze_with_claude()` function in `scan.py` to change what types of projects are flagged as interesting.

## Rate Limits

- **GitHub API**: 5000 requests/hour with authentication
- **Anthropic API**: Varies by plan

The scanner makes approximately:
- 6 GitHub API calls (one per search query)
- 1 Anthropic API call per run

## License

MIT
