from typing import List

def log_event(state: dict, message: str) -> dict:
    """Prints a message to console and appends it to the state logs."""
    # Print to console (strip icons for console if needed, but keeping for now)
    print(message)
    
    # Get current logs or init empty
    logs = state.get("logs") or []
    
    # Append message
    new_logs = list(logs)
    new_logs.append(message)
    
    return {"logs": new_logs}
