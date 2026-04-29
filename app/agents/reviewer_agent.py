from app.core.llm import call_llm

def reviewer_agent(state):
    print("│")
    print("├─ [REVIEW] 🔍 Started — reviewing code...")

    code = state.get("code", "")

    prompt = f"""
    You are a senior code reviewer.

    Review the following Android code and give feedback:
    - Code quality
    - Architecture issues
    - Improvements

    Code:
    {code}
    """

    review_result = call_llm(prompt)

    # --- DEBUG (uncomment for debugging) ---
    # print(f"├─ [REVIEW] DEBUG code length: {len(code)} chars")
    # print(f"├─ [REVIEW] DEBUG review length: {len(review_result)} chars")
    # print(f"├─ [REVIEW] DEBUG review preview: {review_result[:200]}")

    print("├─ [REVIEW] ✅ Completed — review generated")

    return {"review_result": review_result}