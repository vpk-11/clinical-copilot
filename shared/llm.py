"""
Central LLM config. All agents import `chat` from here.
Swap models by setting LLM_MODEL in .env — no agent code changes needed.

Examples:
  LLM_MODEL=anthropic/claude-sonnet-4-20250514   (default)
  LLM_MODEL=openai/gpt-4o
  LLM_MODEL=groq/openai/gpt-oss-120b
  LLM_MODEL=ollama/llama3
"""
import logging
import os
import re
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
DEFAULT_MAX_TOKENS = 2000
# retried with backoff; auth, bad-request and similar errors fail fast
TRANSIENT_ERRORS = {
    "RateLimitError", "Timeout", "APIConnectionError", "ServiceUnavailableError", "InternalServerError",
}


MAX_RETRY_WAIT_S = 30


def retry_delay(e: Exception, attempt: int) -> float:
    """Honour the provider's "try again in 1m5.2s" / "350ms" hint, else 5s, 10s backoff."""
    m = re.search(r"try again in (?:(\d+)m)?([\d.]+)(ms|s)", str(e))
    if m:
        seconds = int(m.group(1) or 0) * 60 + float(m.group(2)) / (1000 if m.group(3) == "ms" else 1)
        return min(seconds + 0.5, MAX_RETRY_WAIT_S)
    return 5 * (attempt + 1)


class LLMTruncated(Exception):
    """Output hit max_tokens or came back empty."""


def chat(
    prompt: str,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    retries: int = 4,
    model: str | None = None,
    api_key: str | None = None,
    fail_on_truncation: bool = False,
) -> str:
    """
    model/api_key: optional per-call overrides (e.g. a caller-supplied BYOK
    key from a request header). Falls back to LLM_MODEL / the provider SDK's
    own env var when not given. Never logged.
    fail_on_truncation: raise LLMTruncated when the output hit max_tokens or is empty
    (reasoning models can spend the whole budget before answering).
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

            choice = resp.choices[0]
            if fail_on_truncation and (
                getattr(choice, "finish_reason", None) == "length" or not (choice.message.content or "").strip()
            ):
                raise LLMTruncated(f"finish_reason={getattr(choice, 'finish_reason', None)}")
            return choice.message.content
        except Exception as e:
            # Never log the prompt (chart text) or api_key — only enough to
            # diagnose which model/provider failed and why.
            logger.warning(
                "llm call failed model=%s byok=%s attempt=%d/%d error=%s: %s",
                model, bool(api_key), attempt + 1, retries, type(e).__name__, e,
            )
            if attempt < retries - 1 and type(e).__name__ in TRANSIENT_ERRORS:
                time.sleep(retry_delay(e, attempt))
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
    if isinstance(e, LLMTruncated):
        return "truncated"
    return "parse_error" if isinstance(e, ValidationError) else f"llm_error ({type(e).__name__})"


def chat_parsed(prompt: str, schema, llm_config: dict | None, **kwargs):
    """
    Returns (validated model | None, degraded reason | None). Never raises.
    Re-runs once based on why the first attempt failed:
      truncated   -> double max_tokens
      parse_error -> same call again (output varies run to run)
      other       -> no re-run (chat() already backs off on transient errors;
                     auth and bad-request errors will not fix themselves)
    """
    llm_config = llm_config or {}
    max_tokens = kwargs.pop("max_tokens", DEFAULT_MAX_TOKENS)
    for attempt in range(2):
        try:
            raw = chat(
                prompt,
                max_tokens=max_tokens,
                model=llm_config.get("model"),
                api_key=llm_config.get("api_key"),
                fail_on_truncation=True,
                **kwargs,
            )
            return parse_json(raw, schema), None
        except Exception as e:
            reason = failure_reason(e)
            logger.warning(
                "llm output degraded schema=%s reason=%s attempt=%d/2", schema.__name__, reason, attempt + 1
            )
            if reason == "truncated":
                max_tokens *= 2
            elif reason != "parse_error":
                break
    return None, reason
