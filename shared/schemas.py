"""Pydantic shapes for LLM JSON output. Mirrors client/src/types.ts."""
from pydantic import BaseModel


class Medication(BaseModel):
    name: str
    dose: str | None = None
    frequency: str | None = None


class MedicationsOut(BaseModel):
    medications: list[Medication]


class TimelineEvent(BaseModel):
    date: str | None = None
    event: str
    category: str | None = None


class TimelineOut(BaseModel):
    events: list[TimelineEvent]


class RiskFlag(BaseModel):
    flag: str
    severity: str | None = None
    evidence: str | None = None


class RiskOut(BaseModel):
    flags: list[RiskFlag]
