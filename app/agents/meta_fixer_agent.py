import os
import subprocess
from app.core.llm import call_llm
from app.core.constants import DEFAULT_MODEL_SMART, DEFAULT_MODEL_FAST, LLM_MAX_TOKENS_META_FIX
from app.tools.github_integration import file_github_issue
from github import Github
from app.core.config import settings

def _run_git_command(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        raise RuntimeError(f"Git command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()

def meta_fixer_agent(exception_traceback: str, failed_file_path: str):
    """
    Level 5 Meta-Fixer Agent: Triggers when the pipeline's Python code throws an exception.
    It reads the failed file, generates a patch, creates a branch, commits, pushes, and opens a PR.
    """
    print("├─ [META-FIXER] 🚨 Pipeline Exception detected! Activating autonomous meta-fixer...")
    
    if not os.path.exists(failed_file_path):
        print(f"├─ [META-FIXER] ❌ Failed to find the offending file: {failed_file_path}")
        return
        
    with open(failed_file_path, "r") as f:
        file_content = f.read()
        
    prompt = f"""
    You are the Meta-Fixer Agent. The Python codebase you are running on has crashed with the following exception:
    
    ### Exception Traceback
    ```text
    {exception_traceback}
    ```
    
    ### Offending File Content ({failed_file_path})
    ```python
    {file_content}
    ```
    
    Your task is to fix the crash. Return ONLY the fully corrected content of the file. Do not use markdown code blocks or any conversational text. The output will be written directly to {failed_file_path}.
    """
    
    try:
        print("├─ [META-FIXER] 🧠 Generating patch via gpt-4o...")
        fixed_content = call_llm(prompt, max_tokens=LLM_MAX_TOKENS_META_FIX, model_name=DEFAULT_MODEL_SMART).strip()
        
        if fixed_content.startswith("```python"):
            fixed_content = fixed_content[9:]
        if fixed_content.startswith("```"):
            fixed_content = fixed_content[3:]
        if fixed_content.endswith("```"):
            fixed_content = fixed_content[:-3]
        fixed_content = fixed_content.strip()
            
        branch_name = f"meta-fix/auto-repair-{os.urandom(4).hex()}"
        
        print(f"├─ [META-FIXER] 🌿 Checking out new branch {branch_name}...")
        _run_git_command(f"git checkout -b {branch_name}")
        
        print(f"├─ [META-FIXER] ✍️ Writing fix to {failed_file_path}...")
        with open(failed_file_path, "w") as f:
            f.write(fixed_content)
            
        _run_git_command(f"git add {failed_file_path}")
        _run_git_command(f"git commit -m 'Autonomous fix for crash in {failed_file_path}'")
        
        # We need a remote to push to, but we might be in a local-only setup. 
        # Attempt to push if GITHUB_REPO is set.
        repo_name = getattr(settings, "GITHUB_REPO", os.getenv("GITHUB_REPO"))
        token = getattr(settings, "GITHUB_TOKEN", os.getenv("GITHUB_TOKEN"))
        
        if repo_name and token:
            print(f"├─ [META-FIXER] 🚀 Pushing branch to remote...")
            _run_git_command(f"git push origin {branch_name}")
            
            print(f"├─ [META-FIXER] 📬 Opening Pull Request...")
            g = Github(token)
            repo = g.get_repo(repo_name)
            
            pr = repo.create_pull(
                title=f"[Meta-Fix] Autonomous Crash Repair for {failed_file_path}",
                body=f"The factory crashed due to a Python exception. I have autonomously generated a fix.\n\n### Traceback\n```text\n{exception_traceback}\n```\n\n**Please review this PR manually. Human-in-the-loop validation is required.**",
                head=branch_name,
                base="main" # Assuming main branch
            )
            print(f"├─ [META-FIXER] ✅ PR created successfully: {pr.html_url}")
        else:
            print("├─ [META-FIXER] ⚠️ GITHUB_REPO or GITHUB_TOKEN not set. Fix committed locally but PR not created.")
            
        print("├─ [META-FIXER] 🔙 Reverting to main branch...")
        _run_git_command("git checkout main")
        
    except Exception as e:
        print(f"├─ [META-FIXER] ❌ Meta-fixer encountered an error: {str(e)}")
        print("├─ [META-FIXER] 🔙 Attempting to abort and switch back to main...")
        try:
            _run_git_command("git reset --hard && git checkout main")
        except:
            pass
