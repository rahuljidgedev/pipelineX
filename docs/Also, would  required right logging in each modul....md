Here is the complete, production-grade specification for **Internal Factory Telemetry, Logging Architecture, and Domino UI Event Synchronization**.  
This document defines how the PipelineX Python engine logs every internal state change, token metric, and compiler error, and streams those events to the colorful Domino UI in real time.  
Save this text as FACTORY\_LOGGING\_AND\_DOMINO\_SPEC.md and feed it directly into your **Antigravity** agent panel.

# **🧱 PipelineX: Internal Factory Telemetry & Domino UI Specification**

> **ANTIGRAVITY DIRECTIVE:** Implement this structured logging framework and Event Bus architecture in the pipelinex-research-factory / pipelinex codebase. All orchestrator nodes, scrapers, and build scripts must emit structured events to drive both local maintainability logs and the real-time Domino UI Dashboard.

## **1\. Factory Logging Architecture (Internal Telemetry)**

To maintain and debug the autonomous software factory without cluttering human-facing interfaces, the engine implements a dual-stream logging architecture:

> 1. **Developer Audit Log (logs/factory\_audit.jsonl):** Structured JSON lines containing complete stack traces, token consumption, execution latencies, and API rate-limit statuses.  
> 2. **Domino UI Event Stream (/api/v1/stream via FastAPI SSE):** Real-time, lightweight Server-Sent Events (SSE) that trigger visual domino flips and plain-English status ticker updates.

┌────────────────────────────────────────────────────────────────────────┐  
│                        PIPELINEX ENGINE NODE                           │  
└────────────────────────────────────────────────────────────────────────┘  
                                    │  
                       emit\_factory\_event(...)  
                                    │  
          ┌─────────────────────────┴─────────────────────────┐  
          ▼                                                   ▼  
┌───────────────────────────────────┐               ┌───────────────────┐  
│     Developer Audit Logger        │               │  Domino Event Bus │  
│   (logs/factory\_audit.jsonl)      │               │   (FastAPI SSE)   │  
└───────────────────────────────────┘               └───────────────────┘  
          │                                                   │  
          ▼                                                   ▼  
\[ Deep Debugging / Auditing \]                       \[ Real-Time Domino UI \]

## **2\. Event Payload Schema**

Every action executed by the orchestrator MUST generate a structured event matching this schema:

JSON  
{  
  "run\_id": "RUN-2026-0813-9821",  
  "timestamp": "2026-08-13T16:00:00Z",  
  "module\_id": "MODULE\_4\_SDLC",  
  "domino\_step": 6,  
  "domino\_name": "Self-Healing Workshop",  
  "state": "REPAIRING",  
  "retry\_count": 1,  
  "max\_retries": 3,  
  "plain\_english\_translation": "The AI caught a missing Kotlin import line in CsvParser.kt. Applying auto-fix...",  
  "telemetry": {  
    "api\_calls\_made": 14,  
    "tokens\_consumed": 18420,  
    "current\_rpm\_status": "4/15 RPM",  
    "execution\_time\_ms": 1240  
  },  
  "technical\_payload": {  
    "file\_affected": "shared/src/commonMain/kotlin/CsvParser.kt",  
    "error\_class": "UnresolvedReferenceException",  
    "raw\_gradle\_line": "e: /CsvParser.kt: (12, 5): Unresolved reference: KtorClient"  
  }  
}

## **3\. Domino UI State Machine & Colors**

The Domino UI consumes state fields from the SSE stream to render exact visual cards and animations:

| State Code | Domino Color | Visual Animation | Meaning |
| :---- | :---- | :---- | :---- |
| IDLE | ⚪ Slate Grey | Static card standing upright | Waiting for its turn in the pipeline sequence. |
| WORKING | 🟡 Glowing Amber | Pulsing border \+ animated wave | AI is actively scraping, generating code, or testing. |
| PASSED | 🟢 Emerald Green | Card tilts down with a checkmark | Step completed successfully with 100% verification. |
| HITL\_PAUSE | 🟠 Bright Orange | Glowing outline \+ chime alert | System paused awaiting human decision (Gate 1 or 2). |
| REPAIRING | 🔴 Coral Red | Circular progress ticker (1/3) | Self-healing loop active; fixing compiler/linter error. |
| FAILED | 💀 Crimson Red | Alert badge \+ recovery button | Hard failure reached max retries ($3/3$). Awaits human help. |

## **4\. Complete Domino Chain Mapping & Plain-English Translations**

### **1️⃣ Domino 1: Market Radar (MODULE\_1\_IDEATION)**

* **Log Level:** INFO  
* **Events Logged:** Review scraping start/end, complaint extraction count, trend keyword velocity.  
* **Domino Ticker:** *"Scanning 1,200 Play Store reviews... Found 142 complaints about offline CSV exports\!"*

### **2️⃣ Domino 2: Legal & Policy Shield (MODULE\_2\_RESEARCH)**

* **Log Level:** INFO / WARN  
* **Events Logged:** Patent database query status, trademark collision checks, Google Play AI policy evaluation.  
* **Domino Ticker:** *"Checked 90M global patents... 0 Conflicts found\! Play Store AI Policy: 100% Compliant."*

### **3️⃣ Domino 3: Executive Boardroom (MODULE\_3\_HITL\_GATE\_1)**

* **Log Level:** AUDIT  
* **Events Logged:** Pitch deck generation, user query inputs, human Go/No-Go decision timestamps.  
* **Domino Ticker:** *"Ready for your review\! We found a high-demand gap for 'CSVQuick Offline'."*

### **4️⃣ Domino 4: Architect's Blueprint (MODULE\_4\_SPEC)**

* **Log Level:** INFO  
* **Events Logged:** User story generation, SQLDelight table drafting, KMM layer specification.  
* **Domino Ticker:** *"Drafting Clean Architecture blueprint & SQLDelight database schemas..."*

### **5️⃣ Domino 5: Code & Linter Engine (MODULE\_4\_DEV\_QA)**

* **Log Level:** DEBUG / INFO  
* **Events Logged:** Kotlin file creation, Ktlint formatting execution, Detekt code smell score.  
* **Domino Ticker:** *"Writing Kotlin Multiplatform code... Ktlint formatting applied. 0 code smells found."*

### **6️⃣ Domino 6: Self-Healing Workshop (MODULE\_4\_GRADLE)**

* **Log Level:** WARN / ERROR (Self-Healing Triggers)  
* **Events Logged:** Gradle build stdout/stderr, stack trace compaction, retry loop counter, time.sleep(20) delays.  
* **Domino Ticker:** *"Gradle caught a missing import line. The QA Agent is applying a quick fix (Attempt 1/3)..."*

### **7️⃣ Domino 7: Virtual Screen Inspector (MODULE\_4\_UI\_TEST)**

* **Log Level:** INFO  
* **Events Logged:** Robolectric test execution, Compose UI screenshot generation, blank-screen verification.  
* **Domino Ticker:** *"Capturing virtual screenshots... App loaded successfully without blank screens or crashes\!"*

### **8️⃣ Domino 8: Store Launch Vault (MODULE\_4\_STAGING)**

* **Log Level:** AUDIT  
* **Events Logged:** .jks keystore signing, Fastlane build package, Privacy Policy HTML generation, Play Console setup guide output.  
* **Domino Ticker:** *"Signed Android App Bundle (.aab) created\! Privacy Policy hosted on GitHub Pages."*

### **9️⃣ Domino 9: Live Sentinel (MODULE\_5\_MAINTENANCE)**

* **Log Level:** INFO  
* **Events Logged:** Android Vitals API polling, local dependency version checks, user-initiated email crash-dump receipts.  
* **Domino Ticker:** *"100% Private, Zero-Telemetry active. Monitoring Google Play Vitals for OS compatibility updates."*

## **5\. Implementation Task Checklist for Antigravity**

Antigravity must generate the following telemetry and event bus components inside the repository:

* \[ \] **Create app/telemetry/factory\_logger.py:** A custom Python logging module that writes structured JSON lines to logs/factory\_audit.jsonl.  
* \[ \] **Create app/telemetry/event\_bus.py:** An asynchronous Event Bus using Python's asyncio.Queue to broadcast state events to FastAPI SSE subscribers.  
* \[ \] **Create app/telemetry/translator.py:** A translation utility that takes technical exceptions (e.g., UnresolvedReferenceException) and converts them into friendly, plain-English Domino Ticker strings.  
* \[ \] **Update State Graph Nodes:** Wrap every LangGraph node execution in pipelinex-research-factory / pipelinex with telemetry emitters to continuously push Domino UI state updates.  
* \[ \] **Expose /api/v1/stream in app/api.py:** Add a Server-Sent Events endpoint to stream domino transitions directly to the React/Tailwind frontend.