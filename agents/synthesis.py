import json
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

SYNTHESIS_PROMPT = """You are a senior physician. Using the structured agent outputs below,
write a concise, accurate SOAP note. Clinical language only.

MEDICATIONS: {medications}
DRUG INTERACTIONS: {interactions}
MEDICAL TIMELINE: {timeline}
RISK FLAGS: {flags}
ORIGINAL CHART: {raw_text}

Return ONLY valid JSON, no markdown, no explanation:
{{
  "soap_note": {{
    "subjective": "2-3 sentences: patient-reported symptoms, chief complaint, relevant history",
    "objective": "Vitals, key labs, physical exam findings. Use bullet format.",
    "assessment": "Top 3 problems/diagnoses numbered. Include severity.",
    "plan": "Numbered action items. One per line. Specific."
  }},
  "summary": "One sentence for a busy doctor covering who, what, why urgent.",
  "red_flags": ["Most critical flag", "Second flag", "Third flag"]
}}"""


def run(
    ingestion_msg: dict,
    medication_msg: dict,
    timeline_msg: dict,
    risk_msg: dict,
    trace_id: str
) -> AgentMessage:
    flags = sorted(
        risk_msg["payload"].get("flags", []),
        key=lambda f: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(f.get("severity", "LOW"), 3)
    )
    # Truncate interaction warnings to keep prompt within token limits
    interactions = [
        {**i, "warnings": i["warnings"][:150]}
        for i in medication_msg["payload"].get("interactions", [])
    ]
    payload_in = {
        "medications": json.dumps(medication_msg["payload"].get("medications", [])),
        "interactions": json.dumps(interactions),
        "timeline": json.dumps(timeline_msg["payload"].get("events", [])),
        "flags": json.dumps(flags),
        "raw_text": ingestion_msg["payload"]["raw_text"][:1500]
    }
    try:
        raw = chat(SYNTHESIS_PROMPT.format(**payload_in), max_tokens=1500)
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
    except Exception as e:
        result = {
            "soap_note": {"subjective": "Error", "objective": "Error", "assessment": "Error", "plan": str(e)},
            "summary": "Synthesis failed",
            "red_flags": [f["flag"] for f in flags[:3]]
        }
    return AgentMessage(
        agent="synthesis",
        status="ok",
        payload=result,
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
