from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.graph.main_graph import build_graph
from langgraph.types import Command
import os
import uuid

app = FastAPI(title="AI Software Factory")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

graph = build_graph()

# Track running threads to differentiate between "Idle/Paused" and "Running"
running_threads = set()

# --- Pydantic Models ---
class PRDUpdate(BaseModel):
    prd: str


# --- Background Worker ---
def run_graph_background(thread_id: str, inputs=None, is_resume=False):
    config = {"configurable": {"thread_id": thread_id}}
    try:
        running_threads.add(thread_id)
        if is_resume:
            # inputs here is the resume value
            for event in graph.stream(Command(resume=inputs), config=config):
                pass
        else:
            for event in graph.stream(inputs, config=config):
                pass
    finally:
        if thread_id in running_threads:
            running_threads.remove(thread_id)

# --- Serve Frontend ---
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("app/frontend/index.html")


# --- Pipeline Endpoints ---

@app.post("/start")
def start_pipeline(idea: str, background_tasks: BackgroundTasks):
    thread_id = str(uuid.uuid4())

    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🚀 PIPELINE STARTED (Async)")
    print(f"├─ Idea: {idea}")
    print(f"├─ Thread: {thread_id}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Start in background
    background_tasks.add_task(run_graph_background, thread_id, {"idea": idea})

    return {
        "status": "started",
        "thread_id": thread_id,
    }


@app.get("/status/{thread_id}")
def get_status(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)

    state = dict(snapshot.values) if snapshot.values else {}
    next_nodes = list(snapshot.next) if snapshot.next else []
    
    # If there are no 'next' nodes and it's not in running_threads, it's actually finished
    # If it is in running_threads, it is 'busy'
    is_running = thread_id in running_threads
    
    return {
        "thread_id": thread_id,
        "state": state,
        "next": next_nodes,
        "is_running": is_running,
        "is_completed": len(next_nodes) == 0 and not is_running and len(state) > 0
    }


@app.patch("/prd/{thread_id}")
def update_prd(thread_id: str, body: PRDUpdate):
    config = {"configurable": {"thread_id": thread_id}}
    graph.update_state(config, {"prd": body.prd})
    print(f"├─ [API] ✏️  PRD updated (thread: {thread_id})")
    return {"status": "updated"}


@app.post("/approve/{thread_id}")
def approve(thread_id: str, approved: bool, background_tasks: BackgroundTasks):
    status = "APPROVED" if approved else "REJECTED"
    print("│")
    print(f"├─ [API] 👤 Human decision: {status} (thread: {thread_id})")

    # Start in background
    background_tasks.add_task(run_graph_background, thread_id, {"approved": approved}, is_resume=True)

    return {
        "status": "resumed",
        "thread_id": thread_id
    }


@app.get("/download-app")
def download_app(name: str = "web_app"):
    import shutil
    from fastapi.responses import FileResponse
    
    # Sanitize name for filename
    safe_name = "".join([c for c in name if c.isalnum() or c in (" ", "-", "_")]).strip().replace(" ", "_")
    if not safe_name:
        safe_name = "web_app"
        
    workspace_dir = "workspace"
    zip_path = f"artifacts/{safe_name}"
    
    if not os.path.exists(workspace_dir):
        return {"error": "No project files found"}
    
    os.makedirs("artifacts", exist_ok=True)
    
    # Create zip
    shutil.make_archive(zip_path, 'zip', workspace_dir)
    
    return FileResponse(
        path=f"{zip_path}.zip",
        filename=f"{safe_name}.zip",
        media_type="application/zip"
    )
