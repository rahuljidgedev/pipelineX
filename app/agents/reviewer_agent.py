from app.core.llm import call_llm
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker

def reviewer_agent(state):
    code = state.get("code", "")
    thread_id = state.get("thread_id", "run-1")

    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_STAGING",
        domino_step=8,
        domino_name="Release & Packaging",
        state="WORKING",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_STAGING", "WORKING")
    )

    prompt = f"""
    You are a senior code reviewer.

    Review the following Android code and give feedback:
    - Code quality
    - Architecture issues
    - Improvements

    Code:
    {code}
    """

    try:
        review_result = call_llm(prompt)
    except Exception as e:
        error_msg = f"Reviewer Agent LLM failed: {str(e)}"
        print(f"├─ [REVIEW] ❌ {error_msg}")
        final_logs = log_event(state, f"├─ [REVIEW] ❌ {error_msg}")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_STAGING",
            domino_step=8,
            domino_name="Release & Packaging",
            state="FAILED",
            plain_english_translation=f"Reviewer LLM failed: {str(e)}"
        )
        return {"error": error_msg, "logs": final_logs["logs"]}

    final_logs = log_event(state, "├─ [REVIEW] ✅ Completed — review generated")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_STAGING",
        domino_step=8,
        domino_name="Release & Packaging",
        state="PASSED",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_STAGING", "PASSED")
    )

    return {
        "review_result": review_result,
        "approval_context": "review",
        "logs": final_logs["logs"],
    }
