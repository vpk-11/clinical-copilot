import json

import pytest
import requests

from agents import input as input_agent, medication, risk, synthesis, timeline
from agents.ingestion import run as ingest
from shared.llm import parse_json
from shared.schemas import MedicationsOut

CHART = "MEDICATIONS:\n1. Lisinopril 10mg PO daily\nVITALS:\nHR 120, SpO2 90% on RA\n" + "x" * 50
ING = ingest(CHART)
MED = {"agent": "medication", "payload": {"medications": [], "interactions": []}}
TL = {"agent": "timeline", "payload": {"events": []}}
RISK = {"agent": "risk", "payload": {"flags": []}}

CALLS = {
    "input": lambda: input_agent.run(CHART),
    "medication": lambda: medication.run(ING, "t"),
    "timeline": lambda: timeline.run(ING, "t"),
    "risk": lambda: risk.run(ING, MED, "t"),
    "synthesis": lambda: synthesis.run(ING, MED, TL, RISK, "t"),
}


@pytest.mark.parametrize("name", CALLS)
def test_agent_degrades_when_llm_raises(stub_llm, name):
    stub_llm.error = RuntimeError("boom")
    msg = CALLS[name]()
    assert msg["status"] == "degraded"


@pytest.mark.parametrize("name", ["medication", "timeline", "risk", "synthesis"])
@pytest.mark.parametrize("bad", ["not json", '{"medications": "x", "events": "x", "flags": "x"}', "{}"])
def test_bad_llm_json_is_parse_error(stub_llm, name, bad):
    stub_llm.response = bad
    msg = CALLS[name]()
    assert msg["status"] == "degraded"
    assert msg["payload"]["reason"] == "parse_error"


def test_deterministic_fallback_survives_llm_failure(stub_llm):
    stub_llm.error = RuntimeError("boom")
    msg = risk.run(ING, MED, "t")
    assert {f["flag"] for f in msg["payload"]["flags"]} >= {"Tachycardia", "Hypoxemia"}
    assert medication.run(ING, "t")["payload"]["medications"][0]["name"] == "Lisinopril"


def test_valid_json_passes_through(stub_llm):
    stub_llm.response = '{"flags": [{"flag": "X", "severity": "HIGH", "evidence": "e"}]}'
    msg = risk.run(ING, MED, "t")
    assert msg["status"] == "ok"
    assert "X" in {f["flag"] for f in msg["payload"]["flags"]}


def test_wrong_field_type_rejected():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        parse_json('{"medications": [{"name": 5}]}', MedicationsOut)


def test_openfda_timeout_medication_still_returns(stub_llm):
    stub_llm.response = json.dumps({"medications": [{"name": "Lisinopril"}]})
    msg = medication.run(ING, "t")
    assert msg["status"] == "ok"
    assert msg["payload"]["interactions"] == []
    assert msg["payload"]["medications"][0]["name"] == "Lisinopril"


def test_synthesis_missing_optional_keys_still_ok(stub_llm):
    stub_llm.response = '{"soap_note": {"subjective": "s"}}'
    msg = synthesis.run(ING, MED, TL, RISK, "t")
    assert msg["status"] == "ok"
    assert msg["payload"]["red_flags"] == [] and msg["payload"]["summary"] == ""
