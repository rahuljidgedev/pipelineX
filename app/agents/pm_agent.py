from app.core.llm import call_llm

def pm_agent(state):
    print("│")
    print("├─ [PM] 📝 Started — generating detailed PRD...")

    idea = state.get("idea", "")
    
    prompt = f"""
    You are a senior Product Manager. Create a comprehensive and detailed Product Requirements Document (PRD) for the following app idea:
    "{idea}"
    
    The PRD must include:
    1. Project Overview & Goals
    2. User Personas
    3. Detailed Functional Requirements (Feature by Feature)
    4. Technical Stack Recommendations (Focus on Web technologies: HTML/CSS/JS)
    5. User Interface & Design Guidelines
    6. Future Roadmap
    
    ---
    MANDATORY RULES:
    - Write a COMPLETE and lengthy document. Do not truncate.
    - Use professional, clear language.
    - Format with rich Markdown (headers, lists, tables).
    - Ensure every feature mentioned in the idea is fully expanded into requirements.
    """

    # Increased tokens to 800 for a full document
    prd = call_llm(prompt, max_tokens=800)

    # --- DEBUG (uncomment for debugging) ---
    # print(f"├─ [PM] DEBUG prd length: {len(prd)} chars")

    print("├─ [PM] ✅ Completed — Detailed PRD generated")

    return {"prd": prd}