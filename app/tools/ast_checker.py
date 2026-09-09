import json
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker


def _approval_context_for_attempt(attempts: int) -> str:
    return "qa_exhausted" if attempts >= 3 else "qa_retry"

def ast_checker_node(state):
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
    logs = log_event({**state, **logs}, "├─ [AST] 🔍 Started — Parsing code for structural requirements...")
    
    if not jrc_str:
        logs = log_event({**state, **logs}, "├─ [AST] ❌ FAILED — No JRC found.")
        error_msg = "AST CHECKER FAILED: No JRC was provided, so structural validation cannot run."
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="FAILED",
            plain_english_translation="AST Check Failed: No JRC found."
        )
        return {
            "logs": logs["logs"],
            "ast_result": "fail",
            "error_logs": error_msg,
            "approval_context": _approval_context_for_attempt(attempts),
        }
        
    try:
        jrc = json.loads(jrc_str)
        failed_requirements = []
        
        code_lower = code.lower()
        
        for req in jrc.get("functional_requirements", []):
            indicators = req.get("ui_indicators", [])
            # For each requirement, we expect at least ONE of its indicators to be somewhere in the code
            if indicators:
                found = any(ind.lower() in code_lower for ind in indicators)
                if not found:
                    failed_requirements.append(f"FR '{req.get('id')} - {req.get('feature')}': Missing indicators: {indicators}")
                    
        if failed_requirements:
            logs = log_event({**state, **logs}, f"├─ [AST] ❌ FAILED — Missing structural elements: {len(failed_requirements)}")
            
            error_msg = "AST CHECKER FAILED: The code is missing the following UI indicators:\n" + "\n".join(failed_requirements)
            
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_4_UI_TEST",
                domino_step=7,
                domino_name="Robolectric Virtual Lab",
                state="FAILED",
                plain_english_translation=translate_to_domino_ticker("MODULE_4_UI_TEST", "FAILED", f"Missing {len(failed_requirements)} strict UI indicators.")
            )
            return {
                "ast_result": "fail",
                "error_logs": error_msg,
                "logs": logs["logs"],
                "approval_context": _approval_context_for_attempt(attempts),
            }
            
        logs = log_event({**state, **logs}, "├─ [AST] ✅ PASSED — All structural indicators found.")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="PASSED",
            plain_english_translation=translate_to_domino_ticker("MODULE_4_UI_TEST", "PASSED")
        )
        
        return {
            "ast_result": "pass",
            "logs": logs["logs"],
            "approval_context": "ast_passed",
        }
        
    except json.JSONDecodeError:
        logs = log_event({**state, **logs}, "├─ [AST] ❌ FAILED — JRC is invalid JSON.")
        error_msg = "AST CHECKER FAILED: The JRC payload is invalid JSON and cannot be validated."
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_UI_TEST",
            domino_step=7,
            domino_name="Robolectric Virtual Lab",
            state="FAILED",
            plain_english_translation="AST Check Failed: Invalid JRC JSON."
        )
        
        return {
            "ast_result": "fail",
            "error_logs": error_msg,
            "logs": logs["logs"],
            "approval_context": _approval_context_for_attempt(attempts),
        }
