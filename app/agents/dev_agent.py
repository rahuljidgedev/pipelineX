from app.core.llm import call_llm

def dev_agent(state):
    error_logs = state.get("error_logs")
    prd = state.get("prd", "")
    attempts = state.get("attempts", 0)

    if error_logs:
        print("│")
        print(f"├─ [DEV] 🔧 Started — fixing web code (attempt {attempts})...")

        prompt = f"""
        Fix the Web project based on the errors:

        Error logs/Feedback:
        {error_logs}

        Previous code:
        {state.get("code")}
        
        ---
        MANDATORY: Return the FULL FIXED project files. Do not truncate any file.
        """
    else:
        print("│")
        print("├─ [DEV] 💻 Started — generating complete Web code...")

        prompt = f"""
        You are a senior Web developer.
        Create a FULLY FUNCTIONAL, complete, and beautiful Single Page Application (SPA) based on this PRD:
        {prd}
        
        ---
        Tech Stack: HTML5, Vanilla CSS3, Vanilla JavaScript (ES6+).
        
        ---
        Project structure:
        - index.html
        - styles.css
        - script.js
        
        ---
        RULES:
        - DO NOT TRUNCATE. Every file must be complete and ready for production.
        - Implement ALL features described in the PRD.
        - Ensure the design is premium (dark mode, animations, responsive).
        - No placeholders. Implement real logic.

        Output format:
        FILE: path/to/file
        <content>
        """

    # Increased tokens to 4000 for complete codebases
    code = call_llm(prompt, max_tokens=4000)

    print("├─ [DEV] ✅ Completed — Full Web code generated")

    return {"code": code}
