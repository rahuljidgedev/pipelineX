from langgraph.types import interrupt


def human_approval_node(state):
    print("│")
    print("├─ [APPROVAL] ⏸ Waiting for human approval...")

    # --- DEBUG (uncomment for debugging) ---
    # print(f"├─ [APPROVAL] DEBUG state keys: {list(state.keys())}")
    # print(f"├─ [APPROVAL] DEBUG state: {state}")

    # interrupt() suspends the graph and waits for Command(resume=...)
    # When resumed, it returns the value passed via resume
    answer = interrupt({
        "type": "approval_required",
        "data": state
    })

    approved = answer.get("approved", False)
    status = "✅ Approved" if approved else "❌ Rejected"
    print(f"├─ [APPROVAL] {status}")

    # --- DEBUG (uncomment for debugging) ---
    # print(f"├─ [APPROVAL] DEBUG resume answer: {answer}")
    # print(f"├─ [APPROVAL] DEBUG approved: {approved}")

    return {
        "last_approval": approved
    }