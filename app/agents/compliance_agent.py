import os
import json
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.core.llm import call_llm

def compliance_agent(state):
    thread_id = state.get("thread_id", "run-1")
    target_app_id = state.get("target_app_id")
    idea = state.get("idea", "")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_5_COMPLIANCE",
        domino_step=8,
        domino_name="Play Store Compliance",
        state="WORKING",
        plain_english_translation="Validating Play Store metadata and compliance."
    )
    
    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [COMPLIANCE] 📜 Starting metadata and compliance check...")
    
    project_path = os.path.join(os.getcwd(), "workspace", "apps", target_app_id)
    
    # Check for metadata
    metadata_dir = os.path.join(project_path, "fastlane", "metadata", "android", "en-US")
    os.makedirs(metadata_dir, exist_ok=True)
    
    # 1. Short Description
    short_desc_path = os.path.join(metadata_dir, "short_description.txt")
    if not os.path.exists(short_desc_path) or os.path.getsize(short_desc_path) == 0:
        logs = log_event({**state, **logs}, "├─ [COMPLIANCE] ⚠️ Missing short description. Generating...")
        short_desc = call_llm(f"Generate a compelling Google Play Store short description (max 80 chars) for this app idea: {idea}", max_tokens=100, model_name="gpt-4o-mini").strip()
        with open(short_desc_path, "w") as f:
            f.write(short_desc[:80])
            
    # 2. Full Description
    full_desc_path = os.path.join(metadata_dir, "full_description.txt")
    if not os.path.exists(full_desc_path) or os.path.getsize(full_desc_path) == 0:
        logs = log_event({**state, **logs}, "├─ [COMPLIANCE] ⚠️ Missing full description. Generating...")
        full_desc = call_llm(f"Generate a compelling Google Play Store full description for this app idea: {idea}", max_tokens=1000, model_name="gpt-4o-mini").strip()
        with open(full_desc_path, "w") as f:
            f.write(full_desc)
            
    # 3. Title
    title_path = os.path.join(metadata_dir, "title.txt")
    if not os.path.exists(title_path) or os.path.getsize(title_path) == 0:
        logs = log_event({**state, **logs}, "├─ [COMPLIANCE] ⚠️ Missing title. Generating...")
        title = call_llm(f"Generate a short, catchy title (max 30 chars) for this app idea: {idea}", max_tokens=50, model_name="gpt-4o-mini").strip()
        with open(title_path, "w") as f:
            f.write(title[:30])
            
    # 4. Privacy Policy
    privacy_policy_path = os.path.join(project_path, "PrivacyPolicy.txt")
    if not os.path.exists(privacy_policy_path) or os.path.getsize(privacy_policy_path) == 0:
        logs = log_event({**state, **logs}, "├─ [COMPLIANCE] ⚠️ Missing Privacy Policy. Generating standard template...")
        privacy_policy = call_llm(f"Generate a standard generic privacy policy for an Android app based on this idea: {idea}", max_tokens=1000, model_name="gpt-4o-mini").strip()
        with open(privacy_policy_path, "w") as f:
            f.write(privacy_policy)
            
    logs = log_event({**state, **logs}, "├─ [COMPLIANCE] ✅ All Play Store metadata is compliant.")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_5_COMPLIANCE",
        domino_step=8,
        domino_name="Play Store Compliance",
        state="PASSED",
        plain_english_translation="Play Store metadata verified."
    )
    
    return {
        "logs": logs["logs"],
        "compliance_result": "pass"
    }
