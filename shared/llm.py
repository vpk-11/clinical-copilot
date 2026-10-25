"""
Central LLM config. All agents import `chat` from here.
Swap models by setting LLM_MODEL in .env — no agent code changes needed.

Examples:
  LLM_MODEL=anthropic/claude-sonnet-4-20250514   (default)
  LLM_MODEL=openai/gpt-4o
  LLM_MODEL=groq/llama-3.3-70b-versatile
  LLM_MODEL=ollama/llama3
"""
import logging
import os
import time
from dotenv import load_dotenv
from pydantic import ValidationError

logger = logging.getLogger(__name__)

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


def chat(
    prompt: str,
    max_tokens: int = 1000,
    retries: int = 3,
    model: str | None = None,
    api_key: str | None = None,
) -> str:
    """
    model/api_key: optional per-call overrides (e.g. a caller-supplied BYOK
    key from a request header). Falls back to LLM_MODEL / the provider SDK's
    own env var when not given. Never logged.
    """
    if not _LITELLM_AVAILABLE:
        raise RuntimeError(
            "litellm is not installed. Run: pip install litellm"
        )
    model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
    for attempt in range(retries):
        try:
            t0 = time.time()
            completion_kwargs = dict(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            if api_key:
                completion_kwargs["api_key"] = api_key
            resp = _litellm_completion(**completion_kwargs)
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
            # Never log the prompt (chart text) or api_key — only enough to
            # diagnose which model/provider failed and why.
            logger.warning(
                "llm call failed model=%s byok=%s attempt=%d/%d error=%s: %s",
                model, bool(api_key), attempt + 1, retries, type(e).__name__, e,
            )
            if attempt < retries - 1 and ("rate" in str(e).lower() or "429" in str(e)):
                time.sleep(5 * (attempt + 1))  # 5s, 10s backoff
                continue
            raise


if _OBS_AVAILABLE:
    try:
        chat = _weave.op(name="llm:chat")(chat)
    except Exception:
        pass


def parse_json(raw: str, model):
    """Validate LLM JSON against a pydantic model. Raises ValidationError."""
    raw = raw.replace("```json", "").replace("```", "").strip()
    return model.model_validate_json(raw)


def failure_reason(e: Exception) -> str:
    """Degraded-run reason. Never includes chart text."""
    return "parse_error" if isinstance(e, ValidationError) else f"llm_error ({type(e).__name__})"


def chat_parsed(prompt: str, schema, llm_config: dict | None, **kwargs):
    """Returns (validated model | None, degraded reason | None). Never raises."""
    llm_config = llm_config or {}
    try:
        raw = chat(prompt, model=llm_config.get("model"), api_key=llm_config.get("api_key"), **kwargs)
        return parse_json(raw, schema), None
    except Exception as e:
        reason = failure_reason(e)
        logger.warning("llm output degraded schema=%s reason=%s", schema.__name__, reason)
        return None, reason
