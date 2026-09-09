from app.tools.code_indexer import KotlinCodeIndexer
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker
import os

def repo_context_agent(state):
    idea = state.get("idea", "")
    target_app_id = state.get("target_app_id")
    thread_id = state.get("thread_id", "run-1")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_2_RAG",
        domino_step=2,
        domino_name="Repo Context Analyzer",
        state="WORKING",
        plain_english_translation=translate_to_domino_ticker("MODULE_2_RAG", "WORKING")
    )
    
    if not target_app_id:
        print("├─ [RAG] ⚠️ No target_app_id found. Skipping context extraction.")
        return {"impacted_files": []}
        
    project_path = os.path.join(os.getcwd(), "workspace", "apps", target_app_id)
    if not os.path.exists(project_path):
        print(f"├─ [RAG] ⚠️ Project path {project_path} does not exist.")
        return {"impacted_files": []}
        
    print(f"├─ [RAG] 🔍 Indexing workspace: {project_path}")
    indexer = KotlinCodeIndexer(project_path)
    
    print(f"├─ [RAG] 🧠 Querying for: {idea[:50]}...")
    results = indexer.search(idea, top_k=4)
    
    impacted_files = []
    context_builder = []
    for res in results:
        path = res["path"]
        impacted_files.append(path)
        context_builder.append(f"--- FILE: {path} ---\n```kotlin\n{res['content']}\n```\n")
        
    print(f"├─ [RAG] ✅ Identified {len(impacted_files)} impacted files.")
    
    # We store the context in the 'prd' field if it's maintenance, or we can just pass it as 'jrc' (context)
    # The current graph has 'jrc' (Jira/Context) which we can use for this.
    jrc_context = "\n".join(context_builder)
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_2_RAG",
        domino_step=2,
        domino_name="Repo Context Analyzer",
        state="COMPLETED",
        plain_english_translation=translate_to_domino_ticker("MODULE_2_RAG", "COMPLETED")
    )
    
    return {
        "impacted_files": impacted_files,
        "jrc": jrc_context
    }
