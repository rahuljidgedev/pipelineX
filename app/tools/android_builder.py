import subprocess
import os
import shutil

def setup_gradle_wrapper(project_path: str):
    """Copy the modern Gradle wrapper from templates to the project workspace."""
    template_path = "app/resources/gradle_template"
    if not os.path.exists(template_path):
        print(f"├─ [BUILDER] ⚠️  Gradle template not found at {template_path}")
        return False
    
    try:
        # Copy gradlew
        shutil.copy2(os.path.join(template_path, "gradlew"), os.path.join(project_path, "gradlew"))
        # Copy gradle directory (wrapper jar and properties)
        wrapper_dest = os.path.join(project_path, "gradle", "wrapper")
        os.makedirs(wrapper_dest, exist_ok=True)
        shutil.copy2(os.path.join(template_path, "gradle", "wrapper", "gradle-wrapper.jar"), 
                     os.path.join(wrapper_dest, "gradle-wrapper.jar"))
        shutil.copy2(os.path.join(template_path, "gradle", "wrapper", "gradle-wrapper.properties"), 
                     os.path.join(wrapper_dest, "gradle-wrapper.properties"))
        
        # Ensure it's executable
        os.chmod(os.path.join(project_path, "gradlew"), 0o755)
        print("├─ [BUILDER] ✅ Modern Gradle wrapper (8.2.1) installed in workspace.")
        return True
    except Exception as e:
        print(f"├─ [BUILDER] ❌ Failed to copy Gradle wrapper: {e}")
        return False

def run_gradle_build(project_path: str, app_id: str = None):
    # Ensure modern gradle wrapper is present
    setup_gradle_wrapper(project_path)
    
    # Determine which command to use
    wrapper_path = os.path.join(project_path, "gradlew")
    
    target_module = f":apps:{app_id}" if app_id else ":composeApp"
    cmd_base = ["./gradlew"] if os.path.exists(wrapper_path) else ["gradle"]
    command = cmd_base + [f"{target_module}:assembleDebug", "--no-daemon"]
    
    # Force JAVA_HOME and ANDROID_HOME dynamically
    env = os.environ.copy()
    
    # Priority: System ENV -> Common Linux locations -> Fallback
    # Priority: Specific Android Studio JBR -> Common Linux locations -> System ENV
    jbr_path = "/home/ekalpa/ide/android-studio-panda4/jbr"
    if os.path.exists(jbr_path):
        env["JAVA_HOME"] = jbr_path
    elif "JAVA_HOME" not in env:
        for candidate in ["/usr/lib/jvm/java-17-openjdk-amd64", "/usr/lib/jvm/default-java"]:
            if os.path.exists(candidate):
                env["JAVA_HOME"] = candidate
                break

    if "ANDROID_HOME" not in env:
        for candidate in [
            os.path.expanduser("~/Android/Sdk"),
            "/usr/local/lib/android/sdk",  # Standard GitHub Actions path
            "/home/ekalpa/Android/Sdk"     # Local fallback
        ]:
            if os.path.exists(candidate):
                env["ANDROID_HOME"] = candidate
                break
    
    try:
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=600, # Increased timeout for full builds
            env=env
        )

        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "returncode": result.returncode
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Gradle command not found. Please ensure 'gradle' is installed or gradlew is present."
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Build timeout"
        }

def run_static_analysis(project_path: str):
    """Bypassed: ktlint and detekt are not configured in the golden template."""
    return {
        "success": True,
        "output": "Static analysis bypassed.",
        "error": "",
        "returncode": 0
    }

def cleanup_workspace(project_path: str, app_id: str = None):
    """Garbage Collect local .gradle and build directories to save disk space."""
    paths_to_remove = [
        os.path.join(project_path, ".gradle"),
        os.path.join(project_path, "build"),
    ]
    if app_id:
        paths_to_remove.append(os.path.join(project_path, "apps", app_id, "build"))
    else:
        paths_to_remove.append(os.path.join(project_path, "composeApp", "build"))
    for path in paths_to_remove:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"├─ [GC] ⚠️ Failed to clean {path}: {e}")
    print(f"├─ [GC] ✅ Workspace garbage collection complete.")