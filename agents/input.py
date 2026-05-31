"""
InputAgent: normalizes raw, messy clinical text into structured chart format.
This runs BEFORE the main pipeline. Its output feeds directly into ingestion.run().
"""
import uuid
from datetime import datetime
from shared.models import AgentMessage
from shared.llm import chat

NORMALIZE_PROMPT = """You are a clinical data normalizer. Convert the raw clinical text below into a clean, structured format.

Extract everything available and organize it into these sections (only include sections present in the source):

PATIENT: [full name if found] | DOB: [date if found] | MRN: [MRN if found]
DATE: [encounter date if found] | PROVIDER: [provider name if found]

CHIEF COMPLAINT:
[chief complaint or reason for visit]

HISTORY OF PRESENT ILLNESS:
[HPI narrative — symptoms, duration, context, relevant history]

MEDICATIONS:
[numbered list: Drug dose route frequency — one per line]

VITALS:
[BP, HR, RR, SpO2, Temp, Weight — all on one line]

LABS (TODAY):
[key lab values with units and any critical flags]

PAST MEDICAL HISTORY:
[bullet list of diagnoses with dates if available]

REVIEW OF SYSTEMS:
Positive: [symptoms present]
Negative: [symptoms absent]

PHYSICAL EXAM:
[findings by system]

ASSESSMENT & PLAN:
[numbered problem list with plan for each]

Rules:
- Keep all numbers, values, and clinical detail exactly as in the source — do not invent or hallucinate values
- If a section has no data, omit it entirely
- If the source is already well-structured, preserve the content and just reformat
- Return ONLY the structured text, no explanation, no preamble

Raw clinical text:
{text}"""


def run(raw_text: str, patient_id: str = "ANON") -> AgentMessage:
    trace_id = str(uuid.uuid4())
    try:
        normalized = chat(NORMALIZE_PROMPT.format(text=raw_text[:4000]), max_tokens=1500)
        normalized = normalized.strip()
        if not normalized or len(normalized) < 50:
            normalized = raw_text
    except Exception as e:
        normalized = raw_text

    return AgentMessage(
        agent="input",
        status="ok",
        payload={"normalized_text": normalized, "original_text": raw_text},
        trace_id=trace_id,
        timestamp=datetime.utcnow().isoformat(),
    )
