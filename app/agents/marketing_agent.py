import os
from app.core.llm import call_llm
from app.core.logger import log_event
from app.telemetry.factory_logger import emit_factory_event
from app.telemetry.translator import translate_to_domino_ticker

def marketing_agent(state: dict) -> dict:
    idea = state.get("idea", "")
    prd = state.get("prd", "")
    thread_id = state.get("thread_id", "run-1")
    target_app_id = state.get("target_app_id")

    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_8_MARKETING",
        domino_step=11,
        domino_name="Marketing Engine",
        state="WORKING",
        plain_english_translation="Generating marketing assets (landing page, social posts)..."
    )

    logs = log_event(state, "│")
    logs = log_event({**state, **logs}, "├─ [MARKETING] 🚀 Starting Parallel Marketing Engine...")

    if not target_app_id:
        error_msg = "No target_app_id found. Cannot generate marketing assets."
        logs = log_event({**state, **logs}, f"├─ [MARKETING] ❌ {error_msg}")
        return {"marketing_result": "fail", "logs": logs["logs"]}

    marketing_dir = os.path.join(os.getcwd(), "workspace", "apps", target_app_id, "marketing")
    os.makedirs(marketing_dir, exist_ok=True)

    # 1. Generate Landing Page
    logs = log_event({**state, **logs}, "├─ [MARKETING] 🌐 Generating Landing Page HTML...")
    landing_page_prompt = f"""
You are a world-class copywriter and web developer.
Based on the following app idea and PRD, write a modern, highly-converting landing page in a single HTML file.
Include inline CSS for styling. Make it look beautiful, using modern gradients, a hero section, features section, and a clear call-to-action (CTA) to download the app.

IDEA:
{idea}

PRD EXTRACT:
{prd[:1500]}

Respond ONLY with the raw HTML code. Do not include markdown codeblocks (no ```html).
"""
    landing_page_html = call_llm(landing_page_prompt, max_tokens=3000, model_name="gpt-4o-mini").strip()
    if landing_page_html.startswith("```html"):
        landing_page_html = landing_page_html[7:]
    if landing_page_html.endswith("```"):
        landing_page_html = landing_page_html[:-3]

    with open(os.path.join(marketing_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(landing_page_html.strip())

    # 2. Generate Social Media Posts
    logs = log_event({**state, **logs}, "├─ [MARKETING] 📱 Generating Social Media Campaign...")
    social_prompt = f"""
You are a viral social media manager.
Based on this app idea: "{idea}", write:
1. A catchy Product Hunt launch post (including maker's comment).
2. 3 engaging Twitter/X posts (with emojis and hashtags) to build hype and announce the launch.

Respond ONLY with the text of the posts.
"""
    social_content = call_llm(social_prompt, max_tokens=1500, model_name="gpt-4o-mini").strip()
    
    with open(os.path.join(marketing_dir, "social_campaign.txt"), "w", encoding="utf-8") as f:
        f.write(social_content)

    logs = log_event({**state, **logs}, f"├─ [MARKETING] ✅ Marketing assets saved to {marketing_dir}")
    
    emit_factory_event(
        run_id=thread_id,
        module_id="MODULE_8_MARKETING",
        domino_step=11,
        domino_name="Marketing Engine",
        state="PASSED",
        plain_english_translation="Marketing assets successfully generated."
    )

    return {"marketing_result": "pass", "logs": logs["logs"]}
