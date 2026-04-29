from openai import OpenAI
from app.core.config import settings
import os

api_key = settings.OPENAI_API_KEY

if not api_key:
    raise ValueError("OPENAI_API_KEY is missing!")

client = OpenAI(api_key=api_key)

def call_llm(prompt: str, max_tokens: int = 1000) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                    {"role": "system", "content": "You are a senior software engineer."},
                    {"role": "user", "content": prompt}
                ],
            temperature=0.3,
            max_tokens= max_tokens
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"LLM Error: {str(e)}"
