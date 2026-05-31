import json
import re
import requests
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

EXTRACT_PROMPT = """Return ONLY raw JSON. No prose. No markdown.
Extract ALL medications from this clinical text.
{{"medications": [{{"name": "drug name", "dose": "dose or unknown", "frequency": "frequency or unknown"}}]}}
Text: {text}"""

ACE_INHIBITORS = {"lisinopril", "enalapril", "ramipril", "benazepril", "captopril"}
POTASSIUM_SPARING_DIURETICS = {"spironolactone", "eplerenone", "amiloride", "triamterene"}


def _med_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def _fallback_extract_medications(text: str) -> list:
    match = re.search(r"MEDICATIONS:\s*(.*?)(?:\n[A-Z][A-Z &/()]+:|\Z)", text, re.S)
    if not match:
        return []

    meds = []
    for line in match.group(1).splitlines():
        line = re.sub(r"^\s*\d+\.\s*", "", line).strip()
        if not line:
            continue
        line = re.sub(r"\s*\([^)]*\)", "", line).strip()
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        rest = " ".join(parts[1:]).strip()
        dose_match = re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|g|units?|mL)\b", rest, re.I)
        dose = dose_match.group(0) if dose_match else "unknown"
        frequency = rest[dose_match.end():].strip() if dose_match else rest
        meds.append({"name": name, "dose": dose, "frequency": frequency or "unknown"})
    return meds


def _merge_medications(primary: list, fallback: list) -> list:
    merged = []
    seen = set()
    for med in primary + fallback:
        if not isinstance(med, dict):
            continue
        name = str(med.get("name", "")).strip()
        if not name or name.startswith("parse_error"):
            continue
        key = _med_key(name)
        if key in seen:
            continue
        seen.add(key)
        merged.append({
            "name": name,
            "dose": str(med.get("dose") or "unknown"),
            "frequency": str(med.get("frequency") or "unknown"),
        })
    return merged


def extract_medications(text: str) -> list:
    fallback = _fallback_extract_medications(text)
    try:
        raw = chat(EXTRACT_PROMPT.format(text=text[:2000]))
        raw = raw.replace("```json", "").replace("```", "").strip()
        extracted = json.loads(raw).get("medications", [])
    except Exception:
        extracted = []
    return _merge_medications(extracted, fallback)


def check_interactions(meds: list) -> list:
    interactions = []
    names = {_med_key(m.get("name", "")) for m in meds}
    if names & ACE_INHIBITORS and names & POTASSIUM_SPARING_DIURETICS:
        interactions.append({
            "drug": "lisinopril + spironolactone",
            "warnings": "ACE inhibitor with potassium-sparing diuretic increases hyperkalemia risk; monitor potassium and renal function closely.",
        })
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
