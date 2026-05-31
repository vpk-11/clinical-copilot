import json
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

PROMPT = """Extract a chronological medical timeline from the clinical text below.
Return ONLY valid JSON, no markdown:
{{"events": [{{"date": "YYYY-MM or approximate text", "event": "brief description", "category": "diagnosis|procedure|hospitalization|medication_change|lab|other"}}]}}
Sort oldest first. If no date found, use "unknown".
Text: {text}"""


def run(ingestion_msg: dict, trace_id: str) -> AgentMessage:
    text = ingestion_msg["payload"]["raw_text"]
    try:
        raw = chat(PROMPT.format(text=text[:3000]))
        raw = raw.replace("```json", "").replace("```", "").strip()
        events = json.loads(raw).get("events", [])
    except Exception as e:
        events = [{"date": "error", "event": str(e), "category": "other"}]
    return AgentMessage(
        agent="timeline",
        status="ok",
        payload={"events": events},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
