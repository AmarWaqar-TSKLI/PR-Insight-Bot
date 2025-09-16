# PR Insight Bot: CI/CD Assistant for GitHub PRs

This bot automatically reviews Pull Requests (PRs) using AI, providing improved PR descriptions, code summaries, suggested tests, and code quality notes. It runs as a GitHub Action whenever a PR is opened, edited, or synchronized.

## Features
- AI-powered PR review and summary
- Automated comments on PRs
- Suggestions for missing tests and code quality improvements

## Setup Instructions

### 1. Obtain an OpenRouter API Key
You need an API key from [OpenRouter](https://openrouter.ai/). Sign up and generate your API key.

### 2. Add API Key to GitHub Secrets
1. Go to your GitHub repository.
2. Navigate to **Settings > Secrets and variables > Actions**.
3. Click **New repository secret**.
4. Name the secret `OPENROUTER_API_KEY` and paste your API key as the value.

### 3. Add the Bot Files to Your Project
Copy the following files into your repository:

- `ci_cd_assistant.py` (place in a folder, e.g., `scripts/` or root)
- `ci_cd_assistant.yaml` (place in `.github/workflows/` and rename to `ci_cd_assistant.yaml` if needed)

**Example structure:**
```
.github/
	workflows/
		ci_cd_assistant.yaml
scripts/
	ci_cd_assistant.py
```

> **Note:** Update the path in the workflow file if you place `ci_cd_assistant.py` in a different folder.

### 4. How It Works
1. When you push code and open or update a PR, the GitHub Action runs automatically.
2. The bot checks out your code, sets up Python, installs dependencies, and runs the assistant script.
3. The script uses your API key (from secrets) to call the AI and posts a review comment on the PR.

### 5. Required Environment Variables
These are set automatically by GitHub Actions:
- `GITHUB_REPOSITORY`
- `GITHUB_TOKEN`
- `PR_NUMBER`
- `OPENROUTER_API_KEY` (from your secret)

### 6. Usage
1. Push your code and open a PR against your main branch.
2. The bot will run and post an AI-generated review as a comment on your PR.
3. Merge your PR as usual after review.

## Troubleshooting
- Ensure your API key is valid and named `OPENROUTER_API_KEY` in secrets.
- Check that both files are in the correct paths.
- Review workflow logs in GitHub Actions for errors.

## License
MIT
# PR-Insight-Bot
Developed a GitHub Action that summarizes pull requests,  flags missing tests, and improves commit message quality  to boost developer productivity.
