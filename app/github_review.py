import os

import requests

from app.analyzer import review


class GitHubReviewError(RuntimeError):
    pass


def review_pull_request(repo: str, pr_number: int) -> dict:
    """Review Python files changed in a public/private GitHub PR using a token."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise GitHubReviewError("GITHUB_TOKEN is not configured")

    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}"}
    base = os.getenv("GITHUB_API_URL", "https://api.github.com")
    url = f"{base}/repos/{repo}/pulls/{pr_number}/files"
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    results = []
    for item in response.json():
        filename = item.get("filename", "")
        if not filename.endswith(".py") or item.get("status") == "removed":
            continue
        patch = item.get("patch", "")
        if not patch:
            continue
        # The patch is intentionally reviewed as changed-line context rather than
        # pretending it is the complete file.
        score, findings = review(patch, "python")
        results.append({
            "file": filename,
            "score": score,
            "findings": [f.__dict__ for f in findings],
        })

    return {"repo": repo, "pull_request": pr_number, "files": results}
