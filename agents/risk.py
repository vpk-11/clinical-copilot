import json
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

PROMPT = """You are a clinical decision support system. Analyze for RED FLAGS.

Flag if present:
- Vitals: HR>100 or <60, SBP>180 or <90, SpO2<94%, RR>20
- Labs: K+>5.5 (danger >6.0), Na+<130, Hgb<8, Creatinine>2.5, BNP>500
- High-risk diagnoses: sepsis, PE, STEMI, stroke, DKA, acute CHF decompensation
- Dangerous drug combos: ACE inhibitor + potassium-sparing diuretic (hyperkalemia risk)
- Any mention of "critically high", "STAT", "urgent", "acute"

Return ONLY valid JSON, no markdown:
{{"flags": [{{"flag": "brief name", "severity": "HIGH|MEDIUM|LOW", "evidence": "quoted value or phrase <30 words"}}]}}

HIGH = immediate action needed. Empty array if no flags found.
Text: {text}
Medications: {medications}"""


def run(ingestion_msg: dict, medication_msg: dict, trace_id: str) -> AgentMessage:
    text = ingestion_msg["payload"]["raw_text"]
    meds = json.dumps(medication_msg["payload"]["medications"])
    try:
        raw = chat(PROMPT.format(text=text[:3000], medications=meds))
        raw = raw.replace("```json", "").replace("```", "").strip()
        flags = json.loads(raw).get("flags", [])
    except Exception as e:
        flags = [{"flag": "parse_error", "severity": "LOW", "evidence": str(e)}]
    return AgentMessage(
        agent="risk",
        status="ok",
        payload={"flags": flags},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
