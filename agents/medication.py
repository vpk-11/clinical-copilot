import json
import requests
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

EXTRACT_PROMPT = """Extract ALL medications from this clinical text.
Return ONLY valid JSON, no markdown fences, no explanation:
{{"medications": [{{"name": "drug name", "dose": "dose or unknown", "frequency": "frequency or unknown"}}]}}
Text: {text}"""


def extract_medications(text: str) -> list:
    try:
        raw = chat(EXTRACT_PROMPT.format(text=text[:3000]))
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw).get("medications", [])
    except Exception as e:
        return [{"name": f"parse_error: {str(e)}", "dose": "unknown", "frequency": "unknown"}]


def check_interactions(meds: list) -> list:
    interactions = []
    for m in meds:
        try:
            drug = m["name"].lower().replace(" ", "+")
            url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug}&limit=1"
            r = requests.get(url, timeout=4)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    warnings = results[0].get("drug_interactions", [""])[0][:400]
                    if warnings:
                        interactions.append({"drug": m["name"], "warnings": warnings})
        except Exception:
            pass
    return interactions


def run(ingestion_msg: dict, trace_id: str) -> AgentMessage:
    text = ingestion_msg["payload"]["raw_text"]
    meds = extract_medications(text)
    interactions = check_interactions(meds)
    return AgentMessage(
        agent="medication",
        status="ok",
        payload={"medications": meds, "interactions": interactions},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
