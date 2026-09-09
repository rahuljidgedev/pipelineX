import os
import json
from datetime import datetime

REGISTRY_FILE = "workspace/registry.json"

def get_registry():
    if not os.path.exists(REGISTRY_FILE):
        return []
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def register_app(app_id: str, package_name: str, display_name: str):
    """
    Registers a new app in the workspace registry if it doesn't already exist.
    """
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    registry = get_registry()
    
    # Check for duplicates
    if any(app.get("app_id") == app_id for app in registry):
        return
        
    registry.append({
        "app_id": app_id,
        "package_name": package_name,
        "display_name": display_name,
        "status": "created",
        "creation_date": datetime.utcnow().isoformat() + "Z"
    })
    
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=4)
        
    print(f"├─ [REGISTRY] ✅ Registered app '{app_id}'")
