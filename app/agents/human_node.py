from langgraph.types import interrupt
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker


def human_approval_node(state):
    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [APPROVAL] ⏸ Waiting for human approval...")

    thread_id = state.get("thread_id", "run-1")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_3_HITL_GATE_1",
        domino_step=3,
        domino_name="Interactive Triage Dashboard",
        state="HITL_PAUSE",
        plain_english_translation=translate_to_domino_ticker("MODULE_3_HITL_GATE_1", "HITL_PAUSE")
    )

    # interrupt() suspends the graph and waits for Command(resume=...)
    # When resumed, it returns the value passed via resume
    answer = interrupt({
        "type": "approval_required",
        "data": {**state, "logs": logs["logs"]}
    })

    approved = answer.get("approved", False)
    status_msg = "✅ Approved" if approved else "❌ Rejected"
    
    final_logs = log_event({**state, **logs}, f"├─ [APPROVAL] {status_msg}")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_3_HITL_GATE_1",
        domino_step=3,
        domino_name="Interactive Triage Dashboard",
        state="PASSED" if approved else "FAILED",
        plain_english_translation=translate_to_domino_ticker("MODULE_3_HITL_GATE_1", "PASSED") if approved else "Pitch Rejected."
    )

    return {
        "last_approval": approved,
        "logs": final_logs["logs"]
    }