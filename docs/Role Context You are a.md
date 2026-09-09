# Role & Context
You are a Lead Mobile Systems Engineer working on `@pipelineX`. 

We are optimizing the Human-in-the-Loop (HITL) Android/KMM software factory to operate safely within the **Google AI Studio Free Tier API limits** (strict RPM and Token limits). 

# Immediate Implementation Tasks (Quota & Safety Guardrails)

Please analyze `app/graph/main_graph.py` and the agent definitions, and propose code updates to implement the following guardrails:

1. **Cost-Effective Model Routing:**
   - Configure the `PM Agent` (PRD generation) and `Reviewer Agent` (Final Code Review) to use the heavier `gemini-1.5-pro` model.
   - Configure the `Dev Agent` and `QA Agent` (the repair loop) to use `gemini-1.5-flash` to handle repetitive syntax fixing efficiently.

2. **Strict Gradle Repair Kill Switch:**
   - Ensure the Dev <-> QA fix loop has a strict `attempts` counter. 
   - Set `max_retries = 3`. If Gradle compilation or the AST checker fails 3 times consecutively, the graph must immediately `interrupt()` and surface the error to the human developer. No infinite self-correction loops.

3. **Rate-Limit Smoothing:**
   - Add a 15-second `time.sleep()` delay inside the QA Agent node before it invokes the Dev Agent for a retry, ensuring we do not burst past the 15 Requests Per Minute limit.

4. **Gradle Log Compaction (Token Saver):**
   - Gradle compiler logs can be massive. Update the `QA Agent` to parse and truncate the `error_logs` output. It should extract only the specific lines containing `e:` (errors) or `Exception` stack traces before appending them to the state, preventing context window bloat.

Please provide the precise Python code modifications required to enforce these limits in the graph routing and agent logic.



I envision this product as automated software factory for android.
1) This will be hosted and live all the time.
2) This has ideation module. The idea can be generated from either of following ways -
 a) Researches the web (either use ai or manually web crawling)
 b) Identify pain points
 c) Identifies needs
 d) Identifies social problems
 e) Future research problems
 f) Fully understand the context for these points. You can suggest domains we'll discuss more on it.
 h) Suggeste any other mediums to identify the idea.
 i) Trending in worlds
 j) Solves societal problems.
3) Present it in layman terms. title, summary and description, and sources/references. Ensures it for copyright (that we are not working on anybodies copyright or patented idea). You can create a independent module foe the same, to accurately present it. User and ask queries, request to collect more data and update it, merge with another idea, accept or reject it. Check feasibility of copyright & patent.
4) Once accepted it will go SDLC phase, requirement generation(functional, non- functional), system design, implementation, testing, approval & deployment.

- For each HITL, let us allow human discuss it with you to get more details.
- Suggest any monetization possible.
- Suggest appropriate HITL peat stops in the flow.
- We can exploit full capacity of KMM, python. 
