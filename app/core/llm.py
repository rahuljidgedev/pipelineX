from openai import OpenAI
from google import genai
from app.core.config import settings
from app.core.constants import DEFAULT_MODEL_SMART, DEFAULT_MODEL_FAST
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

provider = settings.LLM_PROVIDER

openai_client = None
gemini_client = None

if provider == "openai":
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing!")
    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
elif provider == "gemini":
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing!")
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def call_llm(prompt: str, max_tokens: int = 1000, model_name: str = DEFAULT_MODEL_SMART) -> str:
    try:
        if provider == "gemini":
            # Hardcoded to gemini-3.6-flash as instructed by the API deprecation error
            gemini_model = "gemini-3.6-flash"

            print(f"    📡 [LLM] Calling {gemini_model} via SDK (max_tokens={max_tokens})...")
            response = gemini_client.models.generate_content(
                model=gemini_model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction="You are a seasoned senior software engineer.",
                    temperature=0.3,
                    max_output_tokens=max_tokens,
                )
            )
            content = response.text
        else:
            print(f"    📡 [LLM] Calling {model_name} (max_tokens={max_tokens})...")
            response = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                        {"role": "system", "content": "You are a senior software engineer."},
                        {"role": "user", "content": prompt}
                    ],
                temperature=0.3,
                max_tokens=max_tokens
            )
            content = response.choices[0].message.content
            
        if not content:
            raise RuntimeError("LLM returned empty response")
        print(f"    ✅ [LLM] Response received ({len(content)} chars)")
        return content

    except Exception as e:
        error_msg = f"LLM call failed: {str(e)}"
        print(f"    ❌ [LLM] {error_msg}")
        raise RuntimeError(error_msg) from e
