import asyncio
from app.graph.main_graph import build_graph
from langgraph.types import Command
import uuid

async def run_test():
    graph = build_graph()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    inputs = {"idea": "A premium Counter app with history using Kotlin Multiplatform and Compose Multiplatform. No web files."}
    
    print(f"🚀 Starting test pipeline for thread: {thread_id}")
    
    current_inputs = inputs
    while True:
        async for event in graph.astream(current_inputs, config=config, stream_mode="values"):
            if "logs" in event:
                print(event["logs"][-1])
        
        snapshot = await graph.aget_state(config)
        if not snapshot.next:
            break
            
        if "prd_approval" in snapshot.next or "build_approval" in snapshot.next:
            print(f"⏸  Detected interrupt at {snapshot.next}. Auto-approving...")
            current_inputs = Command(resume={"approved": True})
        else:
            # Should not happen if everything is connected
            break

    print("✅ Pipeline test complete.")

if __name__ == "__main__":
    asyncio.run(run_test())
