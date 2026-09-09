import os
import shutil
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event

def packaging_node(state: dict) -> dict:
    thread_id = state.get("thread_id", "run-1")
    target_app_id = state.get("target_app_id")

    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_7_PACKAGING",
        domino_step=10,
        domino_name="Packaging Node",
        state="WORKING",
        plain_english_translation="Packaging the compiled app and source code for release..."
    )

    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [PACKAGING] 📦 Starting packaging process...")

    if not target_app_id:
        error_msg = "No target_app_id found. Cannot package."
        logs = log_event({**state, **logs}, f"├─ [PACKAGING] ❌ {error_msg}")
        return {"packaging_result": "fail", "logs": logs["logs"]}

    project_dir = os.path.join(os.getcwd(), "workspace", "apps", target_app_id)
    release_zip = os.path.join(os.getcwd(), "workspace", "apps", f"{target_app_id}_release")

    if not os.path.exists(project_dir):
        logs = log_event({**state, **logs}, f"├─ [PACKAGING] ❌ Source directory {project_dir} does not exist.")
        return {"packaging_result": "fail", "logs": logs["logs"]}

    try:
        # Zip the directory
        shutil.make_archive(release_zip, 'zip', project_dir)
        logs = log_event({**state, **logs}, f"├─ [PACKAGING] ✅ Successfully created {target_app_id}_release.zip")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_7_PACKAGING",
            domino_step=10,
            domino_name="Packaging Node",
            state="PASSED",
            plain_english_translation="App packaged successfully into ZIP."
        )
        return {"packaging_result": "pass", "logs": logs["logs"]}
    except Exception as e:
        logs = log_event({**state, **logs}, f"├─ [PACKAGING] ❌ Packaging failed: {str(e)}")
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_7_PACKAGING",
            domino_step=10,
            domino_name="Packaging Node",
            state="FAILED",
            plain_english_translation=f"Packaging failed: {str(e)}"
        )
        return {"packaging_result": "fail", "logs": logs["logs"]}
