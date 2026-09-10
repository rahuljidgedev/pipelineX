import json
from app.core.llm import call_llm
from app.core.constants import DEFAULT_MODEL_SMART, DEFAULT_MODEL_FAST
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker


def _approval_context_for_attempt(attempts: int) -> str:
    return "qa_exhausted" if attempts >= 3 else "qa_retry"

def auditor_agent(state):
    code = state.get("code", "")
    jrc_str = state.get("jrc", "")
    attempts = state.get("attempts", 0)
    thread_id = state.get("thread_id", "run-1")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_UI_TEST",
        domino_step=7,
        domino_name="Robolectric Virtual Lab",
        state="WORKING",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_UI_TEST", "WORKING")
    )
    
    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [AUDITOR] 🧠 Started — Semantic LLM Code Audit...")
    
    if not jrc_str:
        logs = log_event({**state, **logs}, "├─ [AUDITOR] ❌ FAILED — No JRC found.")
        error_msg = "SEMANTIC AUDITOR FAILED: No JRC was provided, so semantic validation cannot run."
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="FAILED",
            plain_english_translation="Auditor Check Failed: No JRC found."
        )
        return {
            "logs": logs["logs"],
            "auditor_result": "fail",
            "error_logs": error_msg,
            "approval_context": _approval_context_for_attempt(attempts),
        }
        
    prompt = f"""
    You are an independent Quality Assurance Auditor Agent.
    Your job is to semantically verify that the provided Kotlin Multiplatform code FULLY satisfies the JSON Requirements Catalog (JRC).
    
    JRC:
    {jrc_str}
    
    CODE:
    {code}
    
    Task:
    1. Check every functional requirement in the JRC against the CODE.
    2. Does the code logically implement the requirement? 
    3. Output your findings as a strict JSON Conformity Matrix. DO NOT output any other text.
    
    Format:
    ```json
    {{
      "audit_results": [
        {{ "id": "FR-1", "status": "PASSED", "proof_line": "snippet of code proving it" }},
        {{ "id": "FR-2", "status": "FAILED", "reason": "Explanation of what is missing logically" }}
      ]
    }}
    ```
    """
    
    try:
        response = call_llm(prompt, max_tokens=1500, model_name=DEFAULT_MODEL_FAST)
    except Exception as e:
        error_msg = f"Auditor Agent LLM failed: {str(e)}"
        logs = log_event({**state, **logs}, f"├─ [AUDITOR] ❌ {error_msg}")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="FAILED",
            plain_english_translation=f"Auditor LLM failed: {str(e)}"
        )
        
        return {
            "auditor_result": "fail",
            "error_logs": error_msg,
            "logs": logs["logs"],
            "approval_context": _approval_context_for_attempt(attempts),
        }
    
    # Extract JSON Conformity Matrix
    import re
    matrix_json_str = ""
    match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if match:
        matrix_json_str = match.group(1).strip()
    else:
        # Fallback if no code blocks are used
        matrix_json_str = response.strip()
        
    try:
        matrix = json.loads(matrix_json_str)
        failed_items = [res for res in matrix.get("audit_results", []) if res.get("status") == "FAILED"]
        
        if failed_items:
            logs = log_event({**state, **logs}, f"├─ [AUDITOR] ❌ FAILED — Semantic logic missing for {len(failed_items)} requirements.")
            error_msg = "SEMANTIC AUDITOR FAILED: The code is missing logical implementation for the following requirements:\n"
            for item in failed_items:
                error_msg += f"- {item.get('id')}: {item.get('reason')}\n"
            error_msg += "\nPlease modify the code using Targeted Patching to fulfill these missing requirements."
            
            state_val = "REPAIRING" if attempts < 3 else "FAILED"
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_4_UI_TEST",
                domino_step=7,
                domino_name="Robolectric Virtual Lab",
                state=state_val,
                plain_english_translation=translate_to_domino_ticker("MODULE_4_UI_TEST", state_val, f"Missing logic for {len(failed_items)} requirements.")
            )
            
            return {
                "auditor_result": "fail", 
                "conformity_matrix": matrix_json_str, 
                "error_logs": error_msg, 
                "logs": logs["logs"],
                "approval_context": _approval_context_for_attempt(attempts),
            }
            
        logs = log_event({**state, **logs}, "├─ [AUDITOR] ✅ PASSED — Conformity Matrix 100% matched.")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="PASSED",
            plain_english_translation=translate_to_domino_ticker("MODULE_4_UI_TEST", "PASSED")
        )
        
        return {
            "auditor_result": "pass",
            "conformity_matrix": matrix_json_str,
            "logs": logs["logs"],
            "approval_context": "audited_passed",
        }
        
    except json.JSONDecodeError:
        logs = log_event({**state, **logs}, "├─ [AUDITOR] ❌ FAILED — Could not parse conformity matrix.")
        error_msg = "SEMANTIC AUDITOR FAILED: The conformity matrix response was not valid JSON."
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="FAILED",
            plain_english_translation="Auditor Check Failed: Invalid Matrix JSON."
        )
        
        return {
            "auditor_result": "fail",
            "error_logs": error_msg,
            "logs": logs["logs"],
            "approval_context": _approval_context_for_attempt(attempts),
        }
