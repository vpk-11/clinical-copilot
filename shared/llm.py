"""
Central LLM config. All agents import `chat` from here.
Swap models by setting LLM_MODEL in .env — no agent code changes needed.

Examples:
  LLM_MODEL=anthropic/claude-sonnet-4-20250514   (default)
  LLM_MODEL=openai/gpt-4o
  LLM_MODEL=groq/llama-3.3-70b-versatile
  LLM_MODEL=ollama/llama3
"""
import os
import time
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"


def chat(prompt: str, max_tokens: int = 1000, retries: int = 3) -> str:
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    for attempt in range(retries):
        try:
            resp = completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            if attempt < retries - 1 and ("rate" in str(e).lower() or "429" in str(e)):
                time.sleep(2 ** attempt)  # 1s, 2s backoff
                continue
            raise
