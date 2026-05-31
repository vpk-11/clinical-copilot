import json
import re
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

PROMPT = """Return ONLY raw JSON. No prose. No markdown.
You are a clinical decision support system. Analyze for RED FLAGS.

Flag if present:
- Vitals: HR>100 or <60, SBP>180 or <90, SpO2<94%, RR>20
- Labs: K+>5.5 (HIGH when >=6.0), Na+<130, Hgb<8, Creatinine>2.5, BNP>500 (HIGH when >1000)
- High-risk diagnoses: sepsis, PE, STEMI, stroke, DKA, acute CHF decompensation
- Dangerous drug combos: ACE inhibitor + potassium-sparing diuretic (hyperkalemia risk)
- Any mention of "critically high", "STAT", "urgent", "acute"

{{"flags": [{{"flag": "brief name", "severity": "HIGH|MEDIUM|LOW", "evidence": "quoted value or phrase <30 words"}}]}}

HIGH = immediate action needed. Empty array if no flags found.
Text: {text}
Medications: {medications}"""

ACE_INHIBITORS = {"lisinopril", "enalapril", "ramipril", "benazepril", "captopril"}
POTASSIUM_SPARING_DIURETICS = {"spironolactone", "eplerenone", "amiloride", "triamterene"}


def _numbers_after(label: str, text: str) -> list:
    matches = re.findall(rf"\b{re.escape(label)}\s*[:=]?\s*(\d+(?:\.\d+)?)", text, re.I)
    return [float(match) for match in matches]


def _max_number_after(label: str, text: str):
    values = _numbers_after(label, text)
    return max(values) if values else None


def _add_flag(flags: list, flag: str, severity: str, evidence: str) -> None:
    if not any(f["flag"].lower() == flag.lower() for f in flags):
        flags.append({"flag": flag, "severity": severity, "evidence": evidence[:120]})


def _deterministic_flags(text: str, meds: list) -> list:
    flags = []

    potassium = _max_number_after("K", text)
    if potassium is not None and potassium > 5.5:
        severity = "HIGH" if potassium >= 6.0 else "MEDIUM"
        _add_flag(flags, "Hyperkalemia", severity, f"K {potassium:g}")

    spo2 = _max_number_after("SpO2", text)
    if spo2 is not None and spo2 < 94:
        _add_flag(flags, "Hypoxemia", "HIGH", f"SpO2 {spo2:g}% on RA")

    bnp = _max_number_after("BNP", text)
    if bnp is not None and bnp > 500:
        severity = "HIGH" if bnp > 1000 else "MEDIUM"
        _add_flag(flags, "Elevated BNP", severity, f"BNP {bnp:g} pg/mL")

    heart_rate = _max_number_after("HR", text)
    if heart_rate is not None and heart_rate > 100:
        _add_flag(flags, "Tachycardia", "HIGH", f"HR {heart_rate:g}")

    respiratory_rate = _max_number_after("RR", text)
    if respiratory_rate is not None and respiratory_rate > 20:
        _add_flag(flags, "Tachypnea", "MEDIUM", f"RR {respiratory_rate:g}")

    # Blood pressure
    bp_match = re.search(r"\bBP\s+(\d+)/(\d+)", text, re.I)
    if bp_match:
        sbp, dbp = int(bp_match.group(1)), int(bp_match.group(2))
        if sbp > 180:
            _add_flag(flags, "Hypertensive urgency", "HIGH", f"BP {sbp}/{dbp}")
        if sbp < 90:
            _add_flag(flags, "Hypotension", "HIGH", f"BP {sbp}/{dbp} — shock possible")

    # Glucose
    glucose = _max_number_after("Glucose", text)
    if glucose is None:
        glucose = _max_number_after("glucose", text)
    if glucose is not None and glucose > 400:
        _add_flag(flags, "Critical hyperglycemia", "HIGH", f"Glucose {glucose:g} mg/dL")

    # Troponin
    trop = _max_number_after("Troponin I", text)
    if trop is not None and trop > 0.04:
        _add_flag(flags, "Elevated troponin", "HIGH", f"Troponin I {trop:g} ng/mL — myocardial injury")

    # Lactate
    lactate = _max_number_after("Lactate", text)
    if lactate is not None and lactate > 2.0:
        severity = "HIGH" if lactate >= 4.0 else "MEDIUM"
        _add_flag(flags, "Elevated lactate", severity, f"Lactate {lactate:g} mmol/L")

    # Bicarb / acidosis
    bicarb = _max_number_after("Bicarb", text)
    if bicarb is None:
        bicarb = _max_number_after("bicarb", text)
    if bicarb is not None and bicarb < 15:
        _add_flag(flags, "Severe metabolic acidosis", "HIGH", f"Bicarb {bicarb:g} — critical")

    # WBC sepsis
    wbc = _max_number_after("WBC", text)
    if wbc is not None and wbc > 15:
        _add_flag(flags, "Leukocytosis", "MEDIUM", f"WBC {wbc:g} — possible infection/sepsis")

    # Drug combos
    med_names = {str(m.get("name", "")).lower() for m in meds if isinstance(m, dict)}
    if med_names & ACE_INHIBITORS and med_names & POTASSIUM_SPARING_DIURETICS:
        _add_flag(
            flags,
            "ACE inhibitor + potassium-sparing diuretic",
            "HIGH",
            "Lisinopril plus spironolactone increases hyperkalemia risk",
        )

    # Critical diagnoses by keyword
    if re.search(r"acute decompensated CHF|acute CHF", text, re.I):
        _add_flag(flags, "Acute CHF decompensation", "HIGH", "Acute decompensated CHF exacerbation")
    if re.search(r"STEMI|ST elevation", text, re.I):
        _add_flag(flags, "STEMI", "HIGH", "ST elevation myocardial infarction — activate cath lab")
    if re.search(r"septic shock|urosepsis|sepsis protocol", text, re.I):
        _add_flag(flags, "Septic shock", "HIGH", "Sepsis protocol activated")
    if re.search(r"DKA|diabetic ketoacidosis|ketoacidosis", text, re.I):
        _add_flag(flags, "DKA", "HIGH", "Diabetic ketoacidosis confirmed")
    if re.search(r"stroke alert|MCA occlusion|tPA|thrombectomy", text, re.I):
        _add_flag(flags, "Acute ischemic stroke", "HIGH", "Large vessel occlusion — stroke alert")

    return flags


def _merge_flags(primary: list, fallback: list) -> list:
    merged = []
    seen = set()
    for flag in fallback + primary:
        if not isinstance(flag, dict):
            continue
        name = str(flag.get("flag") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        merged.append({
            "flag": name,
            "severity": str(flag.get("severity") or "LOW"),
            "evidence": str(flag.get("evidence") or "")[:120],
        })
    return merged


def run(ingestion_msg: dict, medication_msg: dict, trace_id: str) -> AgentMessage:
    text = ingestion_msg["payload"]["raw_text"]
    medication_list = medication_msg["payload"].get("medications", [])
    meds = json.dumps(medication_list)
    fallback = _deterministic_flags(text, medication_list)
    try:
        raw = chat(PROMPT.format(text=text[:3000], medications=meds))
        raw = raw.replace("```json", "").replace("```", "").strip()
        flags = json.loads(raw).get("flags", [])
    except Exception:
        flags = []
    flags = _merge_flags(flags, fallback)
    return AgentMessage(
        agent="risk",
        status="ok",
        payload={"flags": flags},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat()
    )
