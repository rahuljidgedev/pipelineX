from langgraph.graph import StateGraph, END
from typing import TypedDict

from app.agents.pm_agent import pm_agent
from app.agents.dev_agent import dev_agent
from app.agents.qa_agent import qa_agent
from app.agents.reviewer_agent import reviewer_agent
from app.agents.human_node import human_approval_node
from app.tools.ast_checker import ast_checker_node
from app.agents.auditor_agent import auditor_agent
from app.agents.repo_context_agent import repo_context_agent
from app.agents.compliance_agent import compliance_agent
from app.tools.fastlane_runner import deployment_node
from app.agents.ideation_agent import ideation_filter_node
from app.agents.marketing_agent import marketing_agent
from app.tools.packaging_node import packaging_node
from app.core.constants import PipelineMode
from langgraph.checkpoint.sqlite import SqliteSaver

class State(TypedDict, total=False):
    idea: str
    prd: str
    jrc: str
    code: str
    test_result: str
    ast_result: str
    auditor_result: str
    compliance_result: str
    deployment_result: str
    conformity_matrix: str
    attempts: int
    review_result: str
    error: str
    error_logs: str
    last_approval: bool
    approval_context: str
    logs: list[str]
    thread_id: str
    target_app_id: str
    mode: PipelineMode
    impacted_files: list[str]
    is_feasible: bool
    marketing_result: str
    packaging_result: str

def route_after_qa(state):
    if state.get("error"):
        print("├─ [ROUTER] ⚠️  QA → END (error detected)")
        return END

    if state["test_result"] == "fail":
        attempts = state.get("attempts", 0)

        if attempts < 4:
            print(f"├─ [ROUTER] 🔄 QA → DEV (retry {attempts}/4)")
            return "dev"

        print("├─ [ROUTER] 🛑 QA → BUILD_APPROVAL (max retries reached)")
        return "build_approval"

    print("├─ [ROUTER] ✅ QA → AST (tests passed)")
    return "ast_node"

def route_after_ast(state):
    if state.get("ast_result") == "fail":
        attempts = state.get("attempts", 0)
        if attempts < 4:
            print(f"├─ [ROUTER] 🔄 AST → DEV (retry {attempts}/4)")
            return "dev"
        print("├─ [ROUTER] 🛑 AST → BUILD_APPROVAL (max retries reached)")
        return "build_approval"
    
    print("├─ [ROUTER] ✅ AST → AUDITOR (ast passed)")
    return "auditor_node"

def route_after_auditor(state):
    if state.get("auditor_result") == "fail":
        attempts = state.get("attempts", 0)
        if attempts < 10:
            print(f"├─ [ROUTER] 🔄 AUDITOR → DEV (retry {attempts}/10)")
            return "dev"
        print("├─ [ROUTER] 🛑 AUDITOR → BUILD_APPROVAL (max retries reached)")
        return "build_approval"
    
    print("├─ [ROUTER] ✅ AUDITOR → REVIEW (auditor passed)")
    return "pre_review"

def route_after_prd_approval(state):
    if state.get("last_approval") is True:
        print("├─ [ROUTER] ✅ PRD_APPROVAL → DEV (approved)")
        return "dev"
    print("├─ [ROUTER] ❌ PRD_APPROVAL → END (rejected)")
    return END

def route_after_build_approval(state):
    if state.get("last_approval") is True:
        print("├─ [ROUTER] ✅ BUILD_APPROVAL → COMPLIANCE (approved)")
        return "compliance_node"
    if state.get("approval_context") == "review":
        print("├─ [ROUTER] 🔄 BUILD_APPROVAL → DEV (review rejected, retrying)")
        return "dev"
    # Rejected from a validation-exhaustion path → give up
    print("├─ [ROUTER] ❌ BUILD_APPROVAL → END (rejected after max retries)")
    return END


from app.core.logger import log_event

def route_after_init(state):
    mode = state.get("mode", PipelineMode.GREENFIELD)
    if mode == PipelineMode.MAINTENANCE:
        print("├─ [ROUTER] 🔄 INIT → REPO_CONTEXT (maintenance mode)")
        return "repo_context"
    else:
        print("├─ [ROUTER] 🆕 INIT → IDEATION (greenfield mode)")
        return "ideation_node"
        
def route_after_ideation(state):
    if state.get("error") or state.get("is_feasible") is False:
        print(f"├─ [ROUTER] ❌ IDEATION → END (rejected: {state.get('error', 'Unknown')})")
        return END
    return "pre_pm"

def route_after_pm(state):
    if state.get("error"):
        print(f"├─ [ROUTER] ❌ PM → END (error: {state['error'][:80]})")
        return END
    return "prd_approval"

def route_after_dev(state):
    if state.get("error"):
        print(f"├─ [ROUTER] ❌ DEV → END (error: {state['error'][:80]})")
        return END
    return "pre_qa"

from langgraph.checkpoint.memory import MemorySaver

def build_graph(checkpointer=None):
    if checkpointer:
        memory = checkpointer
    else:
        memory = MemorySaver()
        
    graph = StateGraph(State)

    def init_node(state):
        logs = log_event(state, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logs = log_event({**state, **logs}, "🚀 PIPELINE STARTED (Async)")
        logs = log_event({**state, **logs}, "├─ [INIT] 🏁 Initializing pipeline...")
        return {"attempts": state.get("attempts") or 0, "logs": logs["logs"]}

    def pre_pm(state):
        current_logs = state.get("logs", [])
        logs = log_event(state, "│")
        logs = log_event({**state, **logs}, "├─ [PM] 📝 Started — generating detailed PRD...")
        return {"logs": logs["logs"]}

    def pre_dev(state):
        error_logs = state.get("error_logs")
        attempts = state.get("attempts", 0)
        logs = log_event(state, "│")
        if error_logs:
            logs = log_event({**state, **logs}, f"├─ [ROUTER] 🔄 QA → DEV (Retry {attempts}/10)")
            logs = log_event({**state, **logs}, f"├─ [DEV] 🔧 Started — fixing KMP code (Retry {attempts})...")
        else:
            logs = log_event({**state, **logs}, "├─ [DEV] 💻 Started — generating complete KMP code...")
        return {"logs": logs["logs"]}

    def pre_qa(state):
        attempts = (state.get("attempts") or 0) + 1
        logs = log_event(state, "│")
        attempt_label = "Initial Build" if attempts == 1 else f"Retry {attempts-1}"
        logs = log_event({**state, **logs}, f"├─ [QA] 🧪 Started — validating {attempt_label} (Attempt {attempts}/10)...")
        return {"logs": logs["logs"]}

    def pre_review(state):
        logs = log_event(state, "│")
        logs = log_event({**state, **logs}, "├─ [REVIEW] 🔍 Started — reviewing code...")
        return {"logs": logs["logs"]}

    graph.add_node("init", init_node)
    graph.add_node("ideation_node", ideation_filter_node)
    graph.add_node("repo_context", repo_context_agent)
    graph.add_node("pre_pm", pre_pm)
    graph.add_node("pm", pm_agent)
    graph.add_node("prd_approval", human_approval_node)
    graph.add_node("pre_dev", pre_dev)
    graph.add_node("dev", dev_agent)
    graph.add_node("pre_qa", pre_qa)
    graph.add_node("qa", qa_agent)
    graph.add_node("ast_node", ast_checker_node)
    graph.add_node("auditor_node", auditor_agent)
    graph.add_node("pre_review", pre_review)
    graph.add_node("review_node", reviewer_agent)
    graph.add_node("build_approval", human_approval_node)
    graph.add_node("compliance_node", compliance_agent)
    graph.add_node("packaging_node", packaging_node)
    graph.add_node("marketing_agent", marketing_agent)
    graph.add_node("deployment_node", deployment_node)

    # Entry point
    graph.set_entry_point("init")
    graph.add_conditional_edges("init", route_after_init, {
        "ideation_node": "ideation_node",
        "repo_context": "repo_context"
    })
    
    graph.add_conditional_edges("ideation_node", route_after_ideation, {
        "pre_pm": "pre_pm",
        END: END
    })
    
    # Maintenance flow: repo_context -> dev
    graph.add_edge("repo_context", "pre_dev")

    graph.add_edge("pre_pm", "pm")

    # Flow: PM → error check → approval
    graph.add_conditional_edges("pm", route_after_pm, {
        "prd_approval": "prd_approval",
        END: END
    })
    graph.add_conditional_edges("prd_approval", route_after_prd_approval, {
        "dev": "pre_dev",
        END: END
    })

    # Connect Pre-Nodes to Agents
    graph.add_edge("pre_dev", "dev")
    graph.add_edge("pre_review", "review_node")

    # Flow: Dev → error check → QA loop
    graph.add_conditional_edges("dev", route_after_dev, {
        "pre_qa": "pre_qa",
        END: END
    })
    graph.add_edge("pre_qa", "qa")
    
    graph.add_conditional_edges("qa", route_after_qa, {
        "dev": "pre_dev",
        "ast_node": "ast_node",
        "build_approval": "build_approval",
        END: END
    })
    
    # Flow: AST -> Auditor
    graph.add_conditional_edges("ast_node", route_after_ast, {
        "dev": "pre_dev",
        "auditor_node": "auditor_node",
        "build_approval": "build_approval"
    })
    
    # Flow: Auditor -> Review
    graph.add_conditional_edges("auditor_node", route_after_auditor, {
        "dev": "pre_dev",
        "pre_review": "pre_review",
        "build_approval": "build_approval"
    })

    # Flow: Review → approval
    graph.add_edge("review_node", "build_approval")
    graph.add_conditional_edges("build_approval", route_after_build_approval, {
        "dev": "pre_dev",
        "compliance_node": "compliance_node",
        END: END
    })
    
    # Flow: Compliance -> Packaging -> (Deployment & Marketing in Parallel) -> END
    graph.add_edge("compliance_node", "packaging_node")
    graph.add_edge("packaging_node", "deployment_node")
    graph.add_edge("packaging_node", "marketing_agent")
    
    graph.add_edge("deployment_node", END)
    graph.add_edge("marketing_agent", END)

    return graph.compile(checkpointer=memory)
