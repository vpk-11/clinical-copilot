import re
import uuid
from datetime import datetime
from shared.models import AgentMessage


def run(raw_text: str, patient_id: str = "ANON") -> AgentMessage:
    cleaned = "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in raw_text.splitlines()).strip()
    parts = re.split(r'(?m)(?=^[A-Z][A-Z &/()]+:)', cleaned)
    chunks = [
        s.strip()
        for s in parts
        if len(s.strip()) > 20 and not re.match(r"^(PATIENT|DATE):", s.strip())
    ]
    return AgentMessage(
        agent="ingestion",
        status="ok",
        payload={"chunks": chunks, "raw_text": cleaned, "patient_id": patient_id},
        trace_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat()
    )
