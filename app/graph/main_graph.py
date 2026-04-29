from langgraph.graph import StateGraph, END
from typing import TypedDict

from app.agents.pm_agent import pm_agent
from app.agents.dev_agent import dev_agent
from app.agents.qa_agent import qa_agent
from app.agents.reviewer_agent import reviewer_agent
from app.agents.human_node import human_approval_node
from langgraph.checkpoint.memory import MemorySaver

class State(TypedDict, total=False):
    idea: str
    prd: str
    code: str
    test_result: str
    attempts: int
    review_result: str
    error: str
    error_logs: str
    last_approval: bool

def route_after_qa(state):
    if state.get("error"):
        print("├─ [ROUTER] ⚠️  QA → END (error detected)")
        return END

    if state["test_result"] == "fail":
        attempts = state.get("attempts", 0)

        if attempts < 3:
            print(f"├─ [ROUTER] 🔄 QA → DEV (retry {attempts}/3)")
            return "dev"

        print("├─ [ROUTER] 🛑 QA → BUILD_APPROVAL (max retries reached)")
        return "build_approval"

    print("├─ [ROUTER] ✅ QA → REVIEW (tests passed)")
    return "review_node"

def route_after_prd_approval(state):
    if state.get("last_approval") is True:
        print("├─ [ROUTER] ✅ PRD_APPROVAL → DEV (approved)")
        return "dev"
    print("├─ [ROUTER] ❌ PRD_APPROVAL → END (rejected)")
    return END

def route_after_build_approval(state):
    if state.get("last_approval") is True:
        print("├─ [ROUTER] ✅ BUILD_APPROVAL → END (approved)")
        return END
    # Rejected: retry only if QA passed (came from review path)
    if state.get("test_result") == "pass":
        print("├─ [ROUTER] 🔄 BUILD_APPROVAL → DEV (review rejected, retrying)")
        return "dev"
    # QA exhausted retries AND rejected → give up
    print("├─ [ROUTER] ❌ BUILD_APPROVAL → END (rejected after max retries)")
    return END


memory = MemorySaver()

def build_graph():

    graph = StateGraph(State)

    def init_node(state):
        print("├─ [INIT] 🏁 Initializing pipeline...")
        # --- DEBUG (uncomment for debugging) ---
        # print(f"├─ [INIT] DEBUG state: {state}")
        return {"attempts": state.get("attempts") or 0}

    # Add nodes
    graph.add_node("init", init_node)
    graph.add_node("pm", pm_agent)
    graph.add_node("prd_approval", human_approval_node)
    graph.add_node("dev", dev_agent)
    graph.add_node("qa", qa_agent)
    graph.add_node("review_node", reviewer_agent)
    graph.add_node("build_approval", human_approval_node)

    # Entry point
    graph.set_entry_point("init")
    graph.add_edge("init", "pm")

    # Flow: PRD → approval
    graph.add_edge("pm", "prd_approval")
    graph.add_conditional_edges("prd_approval", route_after_prd_approval)

    # Flow: Dev → QA loop
    graph.add_edge("dev", "qa")
    graph.add_conditional_edges("qa", route_after_qa)

    # Flow: Review → approval
    graph.add_edge("review_node", "build_approval")
    graph.add_conditional_edges("build_approval", route_after_build_approval)

    return graph.compile(checkpointer=memory)