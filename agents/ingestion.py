import re
import uuid
from datetime import datetime
from shared.models import AgentMessage


def run(raw_text: str, patient_id: str = "ANON") -> AgentMessage:
    cleaned = re.sub(r'\s+', ' ', raw_text).strip()
    parts = re.split(r'(?m)(?=^[A-Z][A-Z &/]+:)', cleaned)
    chunks = [s.strip() for s in parts if len(s.strip()) > 20]
    return AgentMessage(
        agent="ingestion",
        status="ok",
        payload={"chunks": chunks, "raw_text": cleaned, "patient_id": patient_id},
        trace_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat()
    )
