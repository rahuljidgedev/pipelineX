import subprocess
import os

def run_docker_build(project_path="sandbox"):
    try:
        # Ensure output dir exists
        os.makedirs("artifacts", exist_ok=True)

        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{os.path.abspath(project_path)}:/app",
                "-v", f"{os.path.abspath('artifacts')}:/output",
                "-w", "/app",
                "android-builder",
                "bash", "-c",
                """
                chmod +x gradlew || true
                ./gradlew assembleDebug --no-daemon --stacktrace

                # Copy APK to output folder
                find . -name "*.apk" -exec cp {} /output/ \\;
                """
            ],
            capture_output=True,
            text=True,
            timeout=1200
        )

        return {
            "success": result.returncode == 0,
            "logs": result.stdout + result.stderr
        }

    except Exception as e:
        return {
            "success": False,
            "logs": str(e)
        }