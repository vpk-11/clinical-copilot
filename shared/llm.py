"""
Central LLM config. All agents import `chat` from here.
Swap models by setting LLM_MODEL in .env — no agent code changes needed.

Examples:
  LLM_MODEL=anthropic/claude-sonnet-4-20250514   (default)
  LLM_MODEL=openai/gpt-4o
  LLM_MODEL=groq/llama-3.1-70b-versatile
  LLM_MODEL=ollama/llama3
"""
import os
from litellm import completion
from dotenv import load_dotenv

load_dotenv()

DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"


def chat(prompt: str, max_tokens: int = 1000) -> str:
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    resp = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content
