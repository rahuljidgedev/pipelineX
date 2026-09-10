import json
import re
from app.core.llm import call_llm
from app.core.constants import DEFAULT_MODEL_SMART, DEFAULT_MODEL_FAST, LLM_MAX_TOKENS_DEFAULT
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker

def ideation_filter_node(state: dict) -> dict:
    raw_idea = state.get("idea", "").strip()
    thread_id = state.get("thread_id", "run-1")

    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_1_IDEATION",
        domino_step=1,
        domino_name="Ideation Triage & Quality Gate",
        state="WORKING",
        plain_english_translation="Evaluating idea feasibility for Kotlin Multiplatform & Android..."
    )

    if not raw_idea or len(raw_idea) < 5:
        error_msg = "Ideation rejected: Provided idea is empty or too short."
        logs = log_event(state, f"├─ [IDEATION] ❌ {error_msg}")
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_1_IDEATION",
            domino_step=1,
            domino_name="Ideation Triage & Quality Gate",
            state="FAILED",
            plain_english_translation="Idea rejected: Input was empty or invalid."
        )
        return {
            "error": error_msg,
            "is_feasible": False,
            "logs": logs["logs"]
        }

    prompt = f"""
You are a Principal Mobile Architect specializing in Kotlin Multiplatform (KMP) and Jetpack Compose.
Evaluate the feasibility of building an Android MVP for the following idea:

IDEA:
"{raw_idea}"

CRITERIA FOR REJECTION (is_feasible = false):
1. Requires external, non-standard physical hardware (e.g. specialized medical devices, proprietary OBD-II dongles, drone controllers). Standard phone sensors (GPS, Camera, Accelerometer, Bluetooth Low Energy) ARE allowed.
2. Involves illegal activities, spyware, or explicit violations of Google Play Developer policies.
3. Completely ambiguous or meaningless input (e.g. "make money fast", "asdfgh").
4. Demands desktop-only or server-only architectures with no client mobile component.

CRITERIA FOR APPROVAL (is_feasible = true):
1. Can be built as a standalone or client-server Android mobile application using KMP and Compose.
2. Core MVP value proposition is clearly identifiable.

OUTPUT FORMAT:
Return strictly a single valid JSON block enclosed in ```json ... ``` with no conversational text:
```json
{{
  "is_feasible": true,
  "confidence_score": 0.95,
  "reason": "Brief technical evaluation reason",
  "refined_idea": "A clear, actionable, and structured version of the idea optimized for PRD generation"
}}
```
"""

    try:
        response = call_llm(prompt, max_tokens=LLM_MAX_TOKENS_DEFAULT, model_name=DEFAULT_MODEL_FAST)
        
        match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
        else:
            json_str = response.strip()
            
        result = json.loads(json_str)
        is_feasible = result.get("is_feasible", False)
        reason = result.get("reason", "No reason provided")
        refined_idea = result.get("refined_idea", raw_idea)
        
        logs = log_event(state, "│")
        if is_feasible:
            logs = log_event({**state, **logs}, f"├─ [IDEATION] ✅ Approved. Reason: {reason}")
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_1_IDEATION",
                domino_step=1,
                domino_name="Ideation Triage & Quality Gate",
                state="PASSED",
                plain_english_translation="Idea is technically feasible."
            )
            return {
                "is_feasible": True,
                "idea": refined_idea,
                "logs": logs["logs"]
            }
        else:
            error_msg = f"Ideation rejected: {reason}"
            logs = log_event({**state, **logs}, f"├─ [IDEATION] ❌ {error_msg}")
            emit_factory_event(
                run_id=thread_id,
                module_id="MODULE_1_IDEATION",
                domino_step=1,
                domino_name="Ideation Triage & Quality Gate",
                state="FAILED",
                plain_english_translation=f"Idea rejected: {reason}"
            )
            return {
                "error": error_msg,
                "is_feasible": False,
                "logs": logs["logs"]
            }
            
    except Exception as e:
        error_msg = f"Ideation filter failed to evaluate: {str(e)}"
        logs = log_event(state, f"├─ [IDEATION] ❌ {error_msg}")
        return {
            "error": error_msg,
            "is_feasible": False,
            "logs": logs["logs"]
        }
