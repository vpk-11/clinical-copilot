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
from dotenv import load_dotenv

try:
    from litellm import completion as _litellm_completion
    _LITELLM_AVAILABLE = True
except ImportError:
    _litellm_completion = None
    _LITELLM_AVAILABLE = False

try:
    import wandb as _wandb
    import weave as _weave
    _OBS_AVAILABLE = True
except ImportError:
    _OBS_AVAILABLE = False

load_dotenv()

DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"


def chat(prompt: str, max_tokens: int = 1000, retries: int = 3) -> str:
    if not _LITELLM_AVAILABLE:
        raise RuntimeError(
            "litellm is not installed. Run: pip install litellm"
        )
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    for attempt in range(retries):
        try:
            t0 = time.time()
            resp = _litellm_completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            latency = time.time() - t0

            if _OBS_AVAILABLE and _wandb.run is not None:
                try:
                    usage = resp.usage or {}
                    _wandb.log({
                        "inference/model":         model,
                        "inference/latency_s":     round(latency, 3),
                        "inference/input_tokens":  getattr(usage, "prompt_tokens", 0),
                        "inference/output_tokens": getattr(usage, "completion_tokens", 0),
                    })
                except Exception:
                    pass

            return resp.choices[0].message.content
        except Exception as e:
            if attempt < retries - 1 and ("rate" in str(e).lower() or "429" in str(e)):
                time.sleep(5 * (attempt + 1))  # 5s, 10s backoff
                continue
            raise


if _OBS_AVAILABLE:
    try:
        chat = _weave.op(name="llm:chat")(chat)
    except Exception:
        pass
