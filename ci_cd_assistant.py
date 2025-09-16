#!/usr/bin/env python3
"""
CI/CD Assistant for GitHub PRs.

Usage (in GitHub Actions): just run the script; environment variables are provided:
 - GITHUB_REPOSITORY  (owner/repo)  (provided automatically)
 - GITHUB_TOKEN       (provided automatically by Actions)
 - PR_NUMBER          (set in workflow)
 - OPENROUTER_API_KEY (set in repo secrets)
"""

import os
import requests
import json
import textwrap
import sys
from typing import List

# Config
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek/deepseek-r1:free"  # adjust if you have different name
MAX_DIFF_CHARS = 20000   # truncate diff length to avoid huge prompts
MAX_PROMPT_TOKENS = 3000  # approximate -- keep prompt compact
AI_MAX_TOKENS = 1500
TEMPERATURE = 0.1

# Env
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
PR_NUMBER = os.getenv("PR_NUMBER")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not GITHUB_REPOSITORY or not GITHUB_TOKEN or not PR_NUMBER or not OPENROUTER_API_KEY:
    print("ERROR: required environment variables missing. Ensure GITHUB_REPOSITORY, GITHUB_TOKEN, PR_NUMBER, and OPENROUTER_API_KEY are set.")
    sys.exit(1)

GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPOSITORY}"

def get_pr_meta(pr_number: str) -> dict:
    url = f"{GITHUB_API_URL}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def get_pr_files_patches(pr_number: str) -> List[dict]:
    # Returns list of files, each with filename and patch (if available)
    url = f"{GITHUB_API_URL}/pulls/{pr_number}/files"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

def build_diff_text(files_json: List[dict], max_chars: int = MAX_DIFF_CHARS) -> str:
    parts = []
    for f in files_json:
        filename = f.get("filename", "<unknown>")
        patch = f.get("patch")
        header = f"\n\n# File: {filename}\n"
        if patch:
            parts.append(header + patch)
        else:
            parts.append(header + f"[no patch available for {filename} (binary or too large)]")
    full = "\n".join(parts)
    if len(full) > max_chars:
        truncated = full[:max_chars]
        truncated += "\n\n...[diff truncated]..."
        return truncated
    return full

def build_prompt(pr_title: str, pr_body: str, diff_text: str) -> str:
    # Keep the prompt concise: include title, short body, and a short diff snippet.
    prompt = textwrap.dedent(f"""
    You are a helpful CI assistant. Given a pull request title, description and code diff, do the following:

    1) Produce an improved PR description (clear, 2-4 sentences).
    2) Provide a short human-readable summary of the code changes (3-6 sentences).
    3) Suggest tests / checks that appear to be missing or desirable (bullet list).
    4) Provide any quick code quality notes (possible bugs, style issues, risky changes).
    
    Reply in Markdown. Use headings:
    ## Improved PR Description
    ## Summary
    ## Suggested Tests
    ## Notes

    PR Title:
    {pr_title}

    PR Description:
    {pr_body}

    Diff (truncated):
    {diff_text}

    IMPORTANT: Keep the answer concise and practical.
    """)
    return prompt

def call_deepseek(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "You are a CI/CD assistant that summarizes diffs and suggests tests."},
            {"role": "user", "content": prompt}
        ],
        "temperature": TEMPERATURE,
        "max_tokens": AI_MAX_TOKENS
    }
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    res = r.json()
    # Try to extract the content safely
    try:
        content = res["choices"][0]["message"]["content"]
    except Exception:
        # if response shape differs, return the raw JSON for debugging
        content = json.dumps(res, indent=2)
    return content

def post_pr_comment(pr_number: str, body: str):
    url = f"{GITHUB_API_URL}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    payload = {"body": body}
    r = requests.post(url, headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()

def main():
    try:
        print(f"Fetching PR #{PR_NUMBER} meta...")
        pr = get_pr_meta(PR_NUMBER)
        pr_title = pr.get("title", "")
        pr_body = pr.get("body", "") or ""
        print("Fetching PR file patches...")
        files = get_pr_files_patches(PR_NUMBER)
        diff_text = build_diff_text(files, MAX_DIFF_CHARS)

        prompt = build_prompt(pr_title, pr_body, diff_text)
        print("Calling DeepSeek for analysis (via OpenRouter)...")
        ai_response = call_deepseek(prompt)

        comment_body = (
            f"## 🤖 CI/CD Assistant Review\n\n"
            f"**PR:** {pr_title}\n\n"
            f"**AI analysis:**\n\n"
            f"{ai_response}\n\n"
            f"*(This comment was generated automatically by the repository's CI/CD Assistant)*"
        )

        print("Posting comment to PR...")
        post = post_pr_comment(PR_NUMBER, comment_body)
        print("Posted comment id:", post.get("id"))
        print("Done.")
    except requests.HTTPError as exc:
        print("HTTP error:", exc.response.status_code, exc.response.text)
        sys.exit(1)
    except Exception as e:
        print("Error:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
