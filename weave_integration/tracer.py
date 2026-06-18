import os
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import wandb as _wandb
    import weave as _weave
    _OBS_AVAILABLE = True
except ImportError:
    _wandb = None
    _weave = None
    _OBS_AVAILABLE = False

_initialized = False


def init_weave():
    global _initialized
    if _initialized:
        return
    if not _OBS_AVAILABLE:
        print("[weave] wandb/weave not installed — tracing disabled")
        return
    try:
        _wandb.init(
            project=os.environ.get("WANDB_PROJECT", "clinical-copilot"),
            name=f"clinicalcopilot-{datetime.utcnow().strftime('%H%M%S')}",
            reinit=True
        )
        _weave.init(os.environ.get("WANDB_PROJECT", "clinical-copilot"))
        _initialized = True
        print("[weave] Initialized successfully")
    except Exception as e:
        print(f"[weave] Init failed (non-blocking): {e}")


def trace_agent(agent_name: str):
    """
    Decorator factory. Wraps an agent run() function with a Weave op.
    Usage: medication.run = trace_agent("medication")(medication.run)
    """
    def decorator(func):
        if not _OBS_AVAILABLE:
            return func
        try:
            traced = _weave.op(name=f"agent:{agent_name}")(func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return traced(*args, **kwargs)

            return wrapper
        except Exception:
            return func

    return decorator
