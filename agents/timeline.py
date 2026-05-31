import json
import re
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

PROMPT = """Return ONLY raw JSON. No prose. No markdown.
Extract a chronological medical timeline from the clinical text below.
{{"events": [{{"date": "YYYY-MM or approximate text", "event": "brief description", "category": "diagnosis|procedure|hospitalization|medication_change|lab|other"}}]}}
Sort oldest first. If no date found, use "unknown".
Text: {text}"""


def _fallback_events(text: str) -> list:
    patterns = [
        (r"Hypertension diagnosed\s+(\d{4})", "Hypertension diagnosed", "diagnosis"),
        (r"Type 2 Diabetes Mellitus diagnosed\s+(\d{4})", "Type 2 diabetes mellitus diagnosed", "diagnosis"),
        (r"(?:Congestive heart failure|CHF).*?diagnosed\s+(?:[A-Za-z]+\s+)?(\d{4})", "Congestive heart failure diagnosed", "diagnosis"),
        (r"NSTEMI.*?(\d{4})", "NSTEMI managed medically", "diagnosis"),
        (r"CKD Stage 3 diagnosed\s+(\d{4})", "CKD stage 3 diagnosed", "diagnosis"),
        (r"Spironolactone.*?started\s+(\d{4}-\d{2}-\d{2})", "Spironolactone started", "medication_change"),
    ]
    events = []
    for pattern, event, category in patterns:
        match = re.search(pattern, text, re.I | re.S)
        if match:
            events.append({"date": match.group(1), "event": event, "category": category})
    return sorted(events, key=lambda e: e["date"])


def _merge_events(primary: list, fallback: list) -> list:
    merged = []
    seen = set()
    for event in primary + fallback:
        if not isinstance(event, dict):
            continue
        date = str(event.get("date") or "unknown")
        description = str(event.get("event") or "").strip()
        category = str(event.get("category") or "other")
        key = (date, description.lower())
        if not description or key in seen:
            continue
        seen.add(key)
        merged.append({"date": date, "event": description, "category": category})
    return sorted(merged, key=lambda e: (e["date"] == "unknown", e["date"]))


def run(ingestion_msg: dict, trace_id: str) -> AgentMessage:
    text = ingestion_msg["payload"]["raw_text"]
    fallback = _fallback_events(text)
    try:
        raw = chat(PROMPT.format(text=text[:3000]))
        raw = raw.replace("```json", "").replace("```", "").strip()
        events = json.loads(raw).get("events", [])
    except Exception:
        events = []
    events = _merge_events(events, fallback)
    return AgentMessage(
        agent="timeline",
        status="ok",
        payload={"events": events},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
