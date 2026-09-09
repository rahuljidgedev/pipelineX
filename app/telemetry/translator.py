def translate_to_domino_ticker(module_id: str, state: str, details: str = None) -> str:
    """
    Translates technical states and exceptions into plain-English Domino Ticker strings.
    """
    if state == "IDLE":
        return f"Waiting in queue for {module_id}."
        
    if module_id == "MODULE_1_IDEATION":
        if state == "WORKING": return "Scanning Play Store reviews for high-friction complaints..."
        if state == "PASSED": return "Found validated user complaints! Extracting core problems..."
        
    elif module_id == "MODULE_2_RESEARCH":
        if state == "WORKING": return "Checking global patents and Google Play AI policy..."
        if state == "PASSED": return "0 Conflicts found! Play Store AI Policy: 100% Compliant."
        
    elif module_id == "MODULE_3_HITL_GATE_1":
        if state == "HITL_PAUSE": return "Ready for your review! We found a high-demand gap."
        if state == "PASSED": return "Pitch Approved. Initiating Software Factory..."
        
    elif module_id == "MODULE_4_SPEC":
        if state == "WORKING": return "Drafting Clean Architecture blueprint & SQLDelight database schemas..."
        if state == "PASSED": return "PRD & Schemas generated successfully."
        
    elif module_id == "MODULE_4_DEV_QA":
        if state == "WORKING": return "Writing Kotlin Multiplatform code... applying Ktlint & Detekt."
        if state == "PASSED": return "Kotlin Multiplatform code written. 0 code smells found."
        
    elif module_id == "MODULE_4_GRADLE":
        if state == "WORKING": return "Executing local Gradle build to verify compilation..."
        if state == "REPAIRING": return f"Gradle caught an error. The QA Agent is applying a quick fix... {details or ''}"
        if state == "PASSED": return "Gradle build successful! App compiles perfectly."
        if state == "FAILED": return "Max retries reached. The AI requires human intervention to fix this bug."
        
    elif module_id == "MODULE_4_UI_TEST":
        if state == "WORKING": return "Capturing virtual screenshots via Robolectric..."
        if state == "PASSED": return "App loaded successfully without blank screens or crashes!"
        
    elif module_id == "MODULE_4_STAGING":
        if state == "WORKING": return "Generating .jks keystore and Fastlane packaging scripts..."
        if state == "PASSED": return "Signed Android App Bundle (.aab) created! Privacy Policy hosted on GitHub Pages."
        
    elif module_id == "MODULE_5_MAINTENANCE":
        if state == "WORKING": return "100% Private, Zero-Telemetry active. Monitoring Google Play Vitals for OS compatibility updates."
        
    return f"Pipeline execution for {module_id} [{state}]: {details or 'Processing...'}"
