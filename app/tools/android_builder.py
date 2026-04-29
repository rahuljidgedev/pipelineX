import subprocess
import os

def run_gradle_build(project_path: str):
    try:
        result = subprocess.run(
            ["./gradlew", "assembleDebug"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Build timeout"
        }