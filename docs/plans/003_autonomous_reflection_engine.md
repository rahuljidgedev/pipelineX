# Autonomous Reflection Engine: Dynamic "Lessons Learned" Knowledge Graph

This plan outlines the architecture for a dynamic, autonomous reflection engine. Instead of hardcoding static prompt rules, the system will organically extract lessons from successful QA retries and store them in a persistent JSON Knowledge Graph (`lessons_learned.json`). 

Based on your excellent feedback, the Knowledge Graph will not just store raw strings. It will act as a highly structured database containing crucial metadata (model used, domain, error signatures) so we can run advanced analytics and filter lessons contextually in the future!

## Proposed Changes

### [Component: Resources]

#### [NEW] [lessons_learned.json](file:///home/ekalpa/Documents/Developer/pipelineX/app/resources/lessons_learned.json)
A persistent JSON file that stores an array of structured lesson objects. Schema example:
```json
[
  {
    "lesson": "Always explicitly import `Modifier` in Compose instead of using wildcards.",
    "domain": "Android/KMP",
    "model": "gpt-4o",
    "error_signature": "Unresolved reference: Modifier",
    "timestamp": "2026-08-13T19:20:00Z"
  }
]
```

### [Component: Agent Workflows]

#### [MODIFY] [qa_agent.py](file:///home/ekalpa/Documents/Developer/pipelineX/app/agents/qa_agent.py)
When the QA agent successfully compiles the project (`build_result["success"] == True`), we will check if `attempts > 1` (meaning it failed previously and the DEV agent just fixed it).
If true, we will:
1. Extract the previous error from `state.get("error_logs")`.
2. Extract the current fixed code from `state.get("code")`.
3. Call a fast LLM (`gpt-4o`) with a prompt to analyze the error and the fix, and extract a concise "Lesson Learned".
4. Determine the metadata:
   - `model`: Read from the current active LLM configuration.
   - `domain`: Hardcoded to "Android/KMP" (or extracted dynamically).
   - `error_signature`: Extract the core error string from the logs.
5. Append this structured JSON object to `app/resources/lessons_learned.json`.

#### [MODIFY] [dev_agent.py](file:///home/ekalpa/Documents/Developer/pipelineX/app/agents/dev_agent.py)
When constructing both the initial prompt and the retry prompt, the DEV agent will load `app/resources/lessons_learned.json`. 
It will parse the JSON, extract the `lesson` strings, and format them as a bulleted list to inject into a new section called `DYNAMIC LESSONS LEARNED (DO NOT REPEAT PAST MISTAKES)`.

## Verification Plan

### Automated Verification
1. I will manually inject a dummy structured JSON object into `lessons_learned.json` to verify it gets correctly parsed and appended to the DEV agent's prompts.
2. I will trigger the `qa_agent.py` logic artificially to ensure the LLM reflection call accurately constructs the JSON object and writes it to disk.

## User Review Required
Please review the updated JSON schema in the implementation plan. Once you hit **Proceed**, I will build this!
