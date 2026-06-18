from typing import TypedDict


class AgentMessage(TypedDict):
    agent: str        # "ingestion" | "medication" | "timeline" | "risk" | "synthesis"
    status: str       # "ok" | "degraded" | "error"
    payload: dict     # agent-specific payload; degraded runs include a "reason" key
    trace_id: str     # UUID4 string — same value for the entire pipeline run
    timestamp: str    # ISO 8601 UTC string
