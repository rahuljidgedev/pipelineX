import json
import os
import asyncio
from datetime import datetime
from app.telemetry.event_bus import domino_event_bus

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "factory_audit.jsonl")

# Ensure logs directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def emit_factory_event(
    run_id: str,
    module_id: str,
    domino_step: int,
    domino_name: str,
    state: str,
    plain_english_translation: str,
    retry_count: int = 0,
    max_retries: int = 3,
    telemetry: dict = None,
    technical_payload: dict = None
):
    """
    Emits a structured JSON event to the local audit log and broadcasts it to the Domino UI.
    """
    if telemetry is None:
        telemetry = {}
    if technical_payload is None:
        technical_payload = {}
        
    event = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "module_id": module_id,
        "domino_step": domino_step,
        "domino_name": domino_name,
        "state": state,
        "retry_count": retry_count,
        "max_retries": max_retries,
        "plain_english_translation": plain_english_translation,
        "telemetry": telemetry,
        "technical_payload": technical_payload
    }
    
    # 1. Developer Audit Log
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
        
    # 2. Domino UI Event Stream (Fire and forget if sync context, else await if in async context)
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(domino_event_bus.publish(event))
    except RuntimeError:
        # Not in an async loop, run it using asyncio.run if necessary, but this might block
        # Since LangGraph is usually run in a thread, we might need a thread-safe publish.
        # But this is a basic implementation. We'll handle thread-safety if needed.
        asyncio.run(domino_event_bus.publish(event))
