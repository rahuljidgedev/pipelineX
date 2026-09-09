from app.core.llm import call_llm
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker
import re
import json

def pm_agent(state):
    idea = state.get("idea", "")
    thread_id = state.get("thread_id", "run-1")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_SPEC",
        domino_step=4,
        domino_name="Architect's Blueprint",
        state="WORKING",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_SPEC", "WORKING")
    )
    
    prompt = f"""
    You are a senior Product Manager. Create a comprehensive and detailed Product Requirements Document (PRD) for the following app idea:
    "{idea}"
    
    The PRD must include:
    1. Project Overview & Goals
    2. User Personas
    3. Detailed Functional Requirements (Feature by Feature)
    4. Technical Stack Recommendations (Focus on Kotlin Multiplatform (KMP) for Android only)
    5. User Interface & Design Guidelines (using Compose Multiplatform)
    6. Future Roadmap
    
    ---
    MANDATORY RULES:
    - THIS IS A KOTLIN MULTIPLATFORM (KMP) PROJECT ONLY. 
    - STRICTLY FORBID ANY WEB (HTML/CSS/JS) REQUIREMENTS OR ARCHITECTURE.
    - Write a COMPLETE and lengthy document. Do not truncate.
    - Code should compile and run.
    - Use professional, clear language.
    - Format with rich Markdown (headers, lists, tables).
    - Ensure every feature mentioned in the idea is fully expanded into requirements.
    
    CRITICAL: You MUST also output a JSON Requirements Catalog (JRC) at the end of your response inside a ```json block. 
    Format:
    ```json
    {{
      "project_id": "app_name",
      "functional_requirements": [
        {{
          "id": "FR-1",
          "feature": "Feature Name",
          "description": "Description",
          "ui_indicators": ["button", "list", "text", "etc"]
        }}
      ]
    }}
    ```
    """

    try:
        # Increased tokens to 3000 for a full document
        response = call_llm(prompt, max_tokens=3000)
    except Exception as e:
        error_msg = f"PM Agent failed: {str(e)}"
        logs = log_event(state, f"├─ [PM] ❌ {error_msg}")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_SPEC",
            domino_step=4,
            domino_name="Architect's Blueprint",
            state="FAILED",
            plain_english_translation=f"Failed to generate specs: {str(e)}"
        )
        return {"error": error_msg, "logs": logs["logs"]}

    # Extract JSON JRC
    jrc_json = ""
    match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if match:
        jrc_json = match.group(1).strip()
    
    # Remove the JSON block from the PRD string
    prd = re.sub(r'```json\n.*?\n```', '', response, flags=re.DOTALL).strip()

    state["logs"] = log_event(state, "├─ [PM] ✅ Completed — Detailed PRD and JRC generated")["logs"]
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_SPEC",
        domino_step=4,
        domino_name="Architect's Blueprint",
        state="PASSED",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_SPEC", "PASSED")
    )

    return {"prd": prd, "jrc": jrc_json, "logs": state["logs"]}