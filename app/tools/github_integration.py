import os
from github import Github
from app.core.config import settings

def file_github_issue(title: str, body: str, labels: list[str] = None):
    """
    Files an issue on the configured GitHub repository.
    Required env vars: GITHUB_TOKEN, GITHUB_REPO (e.g. "username/repo")
    """
    token = getattr(settings, "GITHUB_TOKEN", os.getenv("GITHUB_TOKEN"))
    repo_name = getattr(settings, "GITHUB_REPO", os.getenv("GITHUB_REPO"))
    
    if not token or not repo_name:
        print("├─ [GITHUB] ⚠️ GITHUB_TOKEN or GITHUB_REPO not set. Skipping autonomous issue creation.")
        return None
        
    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        issue = repo.create_issue(
            title=title,
            body=body,
            labels=labels or ["factory-bug", "autonomous"]
        )
        print(f"├─ [GITHUB] ✅ Autonomous issue created: {issue.html_url}")
        return issue.html_url
    except Exception as e:
        print(f"├─ [GITHUB] ❌ Failed to create GitHub issue: {str(e)}")
        return None
