import os
import json
from app.core.llm import call_llm
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker
from app.tools.workspace_customizer import seed_custom_workspace, generate_project_metadata
from app.core.constants import PipelineMode, LLM_MAX_TOKENS_DEV, LESSONS_LEARNED_FILE

def dev_agent(state):
    error_logs = state.get("error_logs")
    review_result = state.get("review_result")
    prd = state.get("prd", "")
    attempts = state.get("attempts", 0)
    idea = state.get("idea", "")
    thread_id = state.get("thread_id", "run-1")
    mode = state.get("mode", PipelineMode.GREENFIELD)
    jrc = state.get("jrc", "")

    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_DEV_QA",
        domino_step=5,
        domino_name="Code & Linter Engine",
        state="WORKING",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_DEV_QA", "WORKING")
    )

    # 1. On initial run (no error logs / attempts == 0), seed and customize the workspace if greenfield
    if not error_logs and attempts == 0 and mode == PipelineMode.GREENFIELD:
        metadata = seed_custom_workspace(idea)
    else:
        metadata = generate_project_metadata(idea)
        
    package_name = metadata["package_name"]
    target_app_id = metadata["app_id"]

    retry_notes = []
    if error_logs:
        retry_notes.append(("Compilation / validation feedback", error_logs))
    if review_result:
        retry_notes.append(("Code review feedback", review_result))

    FORMAT_RULES = """
    Output format:
    STRICTLY follow this format for every file you generate or edit. You MUST use the FILE: marker followed by the path, then the code inside triple backticks.
    
    Example:
    FILE: apps/{target_app_id}/src/commonMain/kotlin/App.kt
    ```kotlin
    package {package_name}

    import androidx.compose.runtime.Composable
    // your code here
    ```
    """

    lessons_block = ""
    lessons_file = LESSONS_LEARNED_FILE
    if os.path.exists(lessons_file):
        try:
            with open(lessons_file, "r") as f:
                lessons = json.load(f)
                if lessons:
                    lessons_block = "\\n\\n--- DYNAMIC LESSONS LEARNED (DO NOT REPEAT PAST MISTAKES) ---\\n"
                    for idx, lesson_obj in enumerate(lessons):
                        lessons_block += f"{idx+1}. {lesson_obj.get('lesson', '')}\\n"
        except Exception as e:
            print(f"├─ [DEV_DEBUG] Failed to load lessons: {e}")

    if retry_notes or mode == PipelineMode.MAINTENANCE:
        feedback_block = "\n\n".join(
            f"{title}:\n{content}" for title, content in retry_notes
        ) if retry_notes else f"MAINTENANCE TASK / BUG REPORT:\n{idea}"
        
        # In maintenance mode, the code context is provided via RAG (jrc), or from the previous code generation
        code_context = state.get("code") or jrc
        
        prompt = f"""
        You are an expert Kotlin Multiplatform architect fixing a compilation/validation failure or implementing a maintenance task.

        TASK / ERROR FEEDBACK:
        {feedback_block}

        CURRENT SOURCE FILES CONTEXT:
        {code_context}
        
        {lessons_block}

        MANDATORY INSTRUCTIONS:
        1. DO NOT output the entire file from scratch.
        2. Output ONLY the targeted modifications using this exact patch format:

        FILE: apps/{target_app_id}/src/commonMain/kotlin/App.kt
        <<<< SEARCH
        ...exact snippet of original code to replace...
        ==== REPLACE
        ...new corrected code...
        >>>> END

        RULES:
        - The SEARCH block must match the existing code character-for-character, including indentation.
        - Never use wildcard imports. Specify explicit imports for each class.
        - Do not touch locked buildscripts or manifests.
        """
    else:
        prompt = f"""
        You are a senior Kotlin Multiplatform (KMP) developer.
        Implement a FULLY FUNCTIONAL, complete, and beautiful Kotlin Multiplatform application based on this PRD:
        {prd}
        
        {lessons_block}
        
        ---
        Tech Stack: Kotlin Multiplatform (KMP), Compose Multiplatform, Kotlin Coroutines.
        Targets: Android ONLY.
        Architecture: Clean Architecture (Data/Domain/Presentation layers), MVI pattern for UI State.
        Testing: Test-Driven Development (TDD). You MUST generate Unit Tests (Kotest, Mockative) and headless Compose UI Tests (Robolectric).

        ---
        PROJECT STATUS & STRUCTURE:
        We have already pre-seeded a compilable, fully customized KMP project inside the workspace for you.
        The package names, namespaces, and basic configuration files have been pre-configured based on the idea.
        
        Your primary task is to generate and implement the business logic and user interface files:
        1. apps/{target_app_id}/src/commonMain/kotlin/App.kt (Main Compose UI and entry point)
        2. Additional helper UI classes or state holders in apps/{target_app_id}/src/commonMain/kotlin/ui/ or apps/{target_app_id}/src/commonMain/kotlin/data/ as needed.
        
        ---
        RULES & BOUNDARIES:
        - Strict Locked Boundaries: You are programmatically BLOCKED from modifying build configuration scripts, Gradle settings, wrappers, properties, or AndroidManifest.xml files. DO NOT output edits to settings.gradle.kts, build.gradle.kts, gradle.properties, or AndroidManifest.xml. Doing so will result in an immediate block.
        - Injectable Territory: You must ONLY generate, edit, or output source files under:
          1. apps/{target_app_id}/src/commonMain/kotlin/App.kt
          2. apps/{target_app_id}/src/commonMain/kotlin/ui/ or apps/{target_app_id}/src/commonMain/kotlin/data/
        - MANDATORY: All source code must be complete, functional, and compilable. Do not truncate.
        - MANDATORY: The main root composable in App.kt MUST be named `App()` because MainActivity explicitly calls it.
        - MANDATORY: You MUST use `package {package_name}` at the top of App.kt.
        - MANDATORY: DO NOT use `@Preview` or `androidx.compose.ui.tooling.preview.Preview` in commonMain code.
        - CRITICAL MANDATORY RULE: NO PLACEHOLDERS ALLOWED. You will instantly fail if you write comments like `// Placeholder for...` or `Text("UI goes here")` or `// TODO`. YOU MUST write the ACTUAL, complete Compose UI code (using TextField, Button, LazyColumn, DropdownMenu, Checkbox, etc.) for EVERY SINGLE requirement in the PRD. Write the full forms and layouts!
        - Ensure the UI is premium using Compose Multiplatform with modern visual aesthetics.
        - NO WEB FILES (No .html, .js, .css).
        
        - MANDATORY IMPORT RULES (Common mistakes to avoid):
          - NEVER USE WILDCARD IMPORTS (e.g. `import androidx.compose.foundation.layout.*`). The static analysis engine (ktlint) will immediately fail your build and reject your code.
          - Because wildcards are banned, you MUST explicitly import EVERY class you use. Do not forget to import `androidx.compose.ui.Modifier` and any specific `androidx.compose.material.icons.filled.*` icons (like `StarBorder`).
          - For state delegation (e.g. `var count by remember { ... }`), you MUST explicitly import:
            import androidx.compose.runtime.getValue
            import androidx.compose.runtime.setValue
            import androidx.compose.runtime.mutableStateOf
            import androidx.compose.runtime.remember
          - For Modifier extension functions (like `clickable`), you MUST explicitly import:
            import androidx.compose.foundation.clickable
          - For sizing units (like `dp`, `sp`), you MUST explicitly import:
            import androidx.compose.ui.unit.dp
            import androidx.compose.ui.unit.sp
          - For Colors (like `Color.Blue`, custom hex colors), you MUST explicitly import:
            import androidx.compose.ui.graphics.Color
          - For standard Material icons, you MUST explicitly import:
            import androidx.compose.material.icons.Icons
            import androidx.compose.material.icons.filled.Add
            import androidx.compose.material.icons.filled.Delete
            import androidx.compose.material.icons.filled.Refresh (or any specific icons you use)
          - Do NOT import Android-specific classes (e.g., `android.graphics.Color` or `android.util.Log`) in commonMain code.
          - CRITICAL DROPDOWN MENU FIX: In Material 3, `DropdownMenuItem` does NOT take a trailing lambda. You MUST use the `text` parameter. Correct: `DropdownMenuItem(text = {{ Text("Item") }}, onClick = {{ ... }})`. Incorrect: `DropdownMenuItem(onClick = {{ ... }}) {{ Text("Item") }}`.
          - CRITICAL TEXTFIELD FIX: NEVER use `BasicTextField`. You MUST use `androidx.compose.material3.TextField` or `androidx.compose.material3.OutlinedTextField`. `BasicTextField` causes `@Composable` context errors with `decorationBox`.
        
        ---
        REQUIRED FILE CHECKLIST (Generate and implement these files):
        1. apps/{target_app_id}/src/commonMain/kotlin/App.kt
        2. apps/{target_app_id}/src/commonTest/kotlin/... (Unit tests)
        3. apps/{target_app_id}/src/androidUnitTest/kotlin/... (Robolectric tests)
        
        ---
        {FORMAT_RULES}
        """

    # Increased tokens to 8000 for complete codebases (KMP is verbose)
    print(f"├─ [DEV_DEBUG] Calling LLM with prompt size: {len(prompt)} chars...")
    try:
        code = call_llm(prompt, max_tokens=LLM_MAX_TOKENS_DEV)
    except Exception as e:
        error_msg = f"Dev Agent LLM failed: {str(e)}"
        print(f"├─ [DEV] ❌ {error_msg}")
        final_logs = log_event(state, f"├─ [DEV] ❌ {error_msg}")
        
        emit_factory_event(
            run_id=thread_id,
            module_id="MODULE_4_DEV_QA",
            domino_step=5,
            domino_name="Code & Linter Engine",
            state="FAILED",
            plain_english_translation=f"LLM Generation Failed: {str(e)}"
        )
        return {"error": error_msg, "logs": final_logs["logs"]}
    print(f"├─ [DEV_DEBUG] LLM generation complete! Output size: {len(code)} chars")
    
    # Check for potential truncation (GPT-4o-mini might stop early)
    is_truncated = len(code) > 20000 or code.strip().endswith("...") 
    if is_truncated:
        print("├─ [DEV_DEBUG] ⚠️  Warning: LLM output might be truncated due to length.")

    # Quick parse check just for console logging
    lines = code.split('\n')
    files_found = [line.replace('FILE:', '').strip() for line in lines if line.startswith('FILE:')]
    print(f"├─ [DEV_DEBUG] Files generated by LLM: {files_found}")

    log_msg = "├─ [DEV] ✅ Completed — Custom KMP code generated"
    if is_truncated:
        log_msg += " (⚠️ Potential truncation detected)"
        
    final_logs = log_event(state, log_msg)
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_4_DEV_QA",
        domino_step=5,
        domino_name="Code & Linter Engine",
        state="PASSED",
        plain_english_translation=translate_to_domino_ticker("MODULE_4_DEV_QA", "PASSED")
    )

    return {
        "code": code, 
        "logs": final_logs["logs"],
        "test_result": None,
        "target_app_id": target_app_id
    }

