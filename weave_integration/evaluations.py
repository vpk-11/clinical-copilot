"""
W&B Weave Evaluations for ClinicalCopilot
------------------------------------------
LLM-as-judge scorers evaluate each agent's output for:
  - clinical_accuracy   : Are diagnoses / flags medically correct?
  - soap_completeness   : Are all four SOAP sections populated and meaningful?
  - flag_relevance      : Are the HIGH risk flags appropriate for this case?
  - medication_safety   : Were dangerous meds flagged / held correctly?

Run:
    python weave_integration/evaluations.py
"""

import asyncio
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

import weave
from weave_integration.tracer import init_weave
from agents.ingestion import run as ing
from agents.medication import run as med
from agents.timeline import run as tl
from agents.risk import run as risk
from agents.synthesis import run as synth
from shared.llm import chat

# ---------------------------------------------------------------------------
# Dataset — one row per clinical case
# ---------------------------------------------------------------------------
DATASET = [
    {
        "id": "case_01_chf",
        "chart_path": "tests/sample_chart.txt",
        "expected_flags": ["hyperkalemia", "bnp", "spo2", "chf"],
        "expected_holds": ["metformin"],
        "case_type": "CHF with hyperkalemia",
    },
    {
        "id": "case_02_sepsis",
        "chart_path": "tests/case_02_sepsis.txt",
        "expected_flags": ["lactate", "sepsis", "hypotension"],
        "expected_holds": ["metformin"],
        "case_type": "Septic shock / urosepsis",
    },
    {
        "id": "case_03_stemi",
        "chart_path": "tests/case_03_stemi.txt",
        "expected_flags": ["troponin", "stemi"],
        "expected_holds": [],
        "case_type": "STEMI",
    },
    {
        "id": "case_04_dka",
        "chart_path": "tests/case_04_dka.txt",
        "expected_flags": ["glucose", "dka", "bicarbonate"],
        "expected_holds": ["metformin"],
        "case_type": "Diabetic ketoacidosis",
    },
    {
        "id": "case_05_stroke",
        "chart_path": "tests/case_05_stroke.txt",
        "expected_flags": ["stroke", "nihss"],
        "expected_holds": [],
        "case_type": "Acute ischemic stroke",
    },
]


# ---------------------------------------------------------------------------
# Model — wraps the full pipeline as a weave.Model
# ---------------------------------------------------------------------------
class ClinicalCopilotModel(weave.Model):
    model_name: str = os.getenv("LLM_MODEL", "groq/llama-3.3-70b-versatile")

    @weave.op()
    def predict(self, chart_path: str, id: str, **kwargs) -> dict:
        text = open(chart_path).read()
        i = ing(text)
        m = med(i, id)
        t = tl(i, id)
        r = risk(i, m, id)
        s = synth(i, m, t, r, id)
        return {
            "soap_note": s["payload"].get("soap_note", {}),
            "summary": s["payload"].get("summary", ""),
            "flags": r["payload"].get("flags", []),
            "medications": m["payload"].get("medications", []),
        }


# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------

@weave.op()
def soap_completeness(output: dict, **kwargs) -> dict:
    """Score 0-1: are all 4 SOAP sections non-empty and not error strings?"""
    soap = output.get("soap_note", {})
    sections = ["subjective", "objective", "assessment", "plan"]
    filled = sum(
        1 for s in sections
        if soap.get(s) and soap[s] not in ("Error", "", "N/A")
    )
    score = filled / len(sections)
    return {"soap_completeness": score, "filled_sections": filled}


@weave.op()
def flag_relevance(output: dict, expected_flags: list, case_type: str, **kwargs) -> dict:
    """LLM judge: are the HIGH flags appropriate for this case type?"""
    flags = output.get("flags", [])
    high_flags = [f["flag"] for f in flags if f.get("severity") == "HIGH"]

    if not high_flags:
        return {"flag_relevance": 0.0, "reason": "No HIGH flags found"}

    prompt = f"""You are a senior physician reviewing an AI clinical decision support system.
Case type: {case_type}
Expected critical findings: {expected_flags}
AI system raised these HIGH flags: {high_flags}

Score from 0.0 to 1.0 how appropriate and complete the AI flags are for this case type.
1.0 = all critical findings correctly flagged, no major misses
0.5 = partially correct, some misses
0.0 = completely wrong or no relevant flags

Reply with ONLY valid JSON: {{"score": <float>, "reason": "<one sentence>"}}"""

    try:
        raw = chat(prompt, max_tokens=150)
        result = json.loads(raw.strip())
        return {"flag_relevance": float(result["score"]), "reason": result.get("reason", "")}
    except Exception as e:
        return {"flag_relevance": 0.5, "reason": f"Judge failed: {e}"}


@weave.op()
def medication_safety(output: dict, expected_holds: list, **kwargs) -> dict:
    """Check if contraindicated meds were flagged for hold."""
    if not expected_holds:
        return {"medication_safety": 1.0, "reason": "No holds expected"}

    meds = output.get("medications", [])
    flagged_names = [
        m["name"].lower()
        for m in meds
        if m.get("interaction_flag") or "hold" in str(m).lower() or "contraindicated" in str(m).lower()
    ]
    # Also check flags
    flag_text = " ".join(f["flag"].lower() for f in output.get("flags", []))

    held = sum(1 for h in expected_holds if h.lower() in flagged_names or h.lower() in flag_text)
    score = held / len(expected_holds)
    return {
        "medication_safety": score,
        "expected_holds": expected_holds,
        "detected": flagged_names,
    }


@weave.op()
def clinical_accuracy(output: dict, case_type: str, **kwargs) -> dict:
    """LLM judge: is the SOAP assessment clinically accurate for the case type?"""
    assessment = output.get("soap_note", {}).get("assessment", "")
    summary = output.get("summary", "")

    if not assessment or assessment == "Error":
        return {"clinical_accuracy": 0.0, "reason": "No assessment generated"}

    prompt = f"""You are a board-certified physician reviewing an AI-generated clinical note.
Case type: {case_type}

AI Assessment section:
{assessment}

AI Summary:
{summary}

Score from 0.0 to 1.0 how clinically accurate and appropriate this assessment is.
1.0 = correct diagnosis, appropriate urgency, no dangerous errors
0.5 = partially correct, minor issues
0.0 = wrong diagnosis or dangerous omission

Reply with ONLY valid JSON: {{"score": <float>, "reason": "<one sentence>"}}"""

    try:
        raw = chat(prompt, max_tokens=150)
        result = json.loads(raw.strip())
        return {"clinical_accuracy": float(result["score"]), "reason": result.get("reason", "")}
    except Exception as e:
        return {"clinical_accuracy": 0.5, "reason": f"Judge failed: {e}"}


# ---------------------------------------------------------------------------
# Run evaluations
# ---------------------------------------------------------------------------

def run_evaluations():
    init_weave()

    model = ClinicalCopilotModel()

    dataset = weave.Dataset(
        name="clinical-cases-v1",
        rows=DATASET,
    )

    evaluation = weave.Evaluation(
        name="ClinicalCopilot-LLM-Judge",
        dataset=dataset,
        scorers=[
            soap_completeness,
            flag_relevance,
            medication_safety,
            clinical_accuracy,
        ],
    )

    print("\n Starting W&B Weave Evaluation (LLM-as-judge)...")
    print(f" Model: {model.model_name}")
    print(f" Cases: {len(DATASET)}")
    print(f" Scorers: soap_completeness, flag_relevance, medication_safety, clinical_accuracy\n")

    results = asyncio.run(evaluation.evaluate(model))

    print("\n Evaluation complete!")
    print(f" View results at: https://wandb.ai/abhale-university-of-massachusetts/clinical-copilot/weave/evaluations")
    return results


if __name__ == "__main__":
    run_evaluations()
