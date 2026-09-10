import os
import subprocess
from app.core.logger import log_event
from app.core.constants import WORKSPACE_DIR, DEFAULT_PACKAGE_PREFIX
from app.telemetry.factory_logger import emit_factory_event
from app.core.config import settings

def _ensure_fastlane_setup(project_path: str, package_name: str):
    fastlane_dir = os.path.join(project_path, "fastlane")
    os.makedirs(fastlane_dir, exist_ok=True)
    
    fastfile_path = os.path.join(fastlane_dir, "Fastfile")
    if not os.path.exists(fastfile_path):
        fastfile_content = f"""
default_platform(:android)

platform :android do
  desc "Submit a new Beta Build to Crashlytics/Play Store"
  lane :beta do
    gradle(task: "clean bundleRelease")
    upload_to_play_store(track: 'beta', skip_upload_images: true, skip_upload_screenshots: true)
  end
end
"""
        with open(fastfile_path, "w") as f:
            f.write(fastfile_content.strip())
            
    appfile_path = os.path.join(fastlane_dir, "Appfile")
    if not os.path.exists(appfile_path):
        appfile_content = f"""
json_key_file("{os.path.join(project_path, 'play-store-credentials.json')}")
package_name("{package_name}")
"""
        with open(appfile_path, "w") as f:
            f.write(appfile_content.strip())
            
def deployment_node(state):
    thread_id = state.get("thread_id", "run-1")
    target_app_id = state.get("target_app_id")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_6_DEPLOY",
        domino_step=9,
        domino_name="Fastlane Deployment",
        state="WORKING",
        plain_english_translation="Deploying to Google Play Store..."
    )
    
    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [DEPLOY] 🚀 Preparing Fastlane Deployment...")
    
    project_path = os.path.join(os.getcwd(), WORKSPACE_DIR, "apps", target_app_id)
    package_name = f"{DEFAULT_PACKAGE_PREFIX}{target_app_id.replace('-', '_')}"
    
    _ensure_fastlane_setup(project_path, package_name)
    
    # Check for credentials
    creds_path = os.path.join(project_path, 'play-store-credentials.json')
    if not os.path.exists(creds_path):
        if getattr(settings, "PLAY_STORE_JSON_KEY", None):
            with open(creds_path, "w") as f:
                f.write(settings.PLAY_STORE_JSON_KEY)
        else:
            logs = log_event({**state, **logs}, "├─ [DEPLOY] ⚠️ PLAY_STORE_JSON_KEY not set. Skipping real deployment.")
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_6_DEPLOY",
                domino_step=9,
                domino_name="Fastlane Deployment",
                state="SKIPPED",
                plain_english_translation="Deployment skipped due to missing credentials."
            )
            return {"logs": logs["logs"], "deployment_result": "skipped"}
            
    logs = log_event({**state, **logs}, "├─ [DEPLOY] 🏃 Running `fastlane beta`...")
    
    try:
        # In a real scenario, this executes fastlane
        result = subprocess.run(["fastlane", "beta"], cwd=project_path, capture_output=True, text=True)
        if result.returncode == 0:
            logs = log_event({**state, **logs}, "├─ [DEPLOY] ✅ Fastlane Deployment Succeeded!")
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_6_DEPLOY",
                domino_step=9,
                domino_name="Fastlane Deployment",
                state="PASSED",
                plain_english_translation="App successfully deployed to Play Store."
            )
            return {"logs": logs["logs"], "deployment_result": "pass"}
        else:
            logs = log_event({**state, **logs}, f"├─ [DEPLOY] ❌ Fastlane Deployment Failed: {result.stderr}")
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_6_DEPLOY",
                domino_step=9,
                domino_name="Fastlane Deployment",
                state="FAILED",
                plain_english_translation="Fastlane deployment failed."
            )
            return {"logs": logs["logs"], "deployment_result": "fail"}
    except FileNotFoundError:
        logs = log_event({**state, **logs}, "├─ [DEPLOY] ⚠️ Fastlane executable not found on system. Skipping real deployment.")
        return {"logs": logs["logs"], "deployment_result": "skipped"}
