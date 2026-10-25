import json
import os

import pytest

from agents.medication import _fallback_extract_medications
from agents.risk import _deterministic_flags
from scripts.eval_flags import ROOT, evaluate

LABELS = json.load(open(os.path.join(ROOT, "tests/eval/labels.json")))
HIGH = {
    "samples/chf-jane-doe__ed-note.txt": "Acute CHF decompensation",
    "samples/sepsis-john-smith__ed-note.txt": "Septic shock",
    "samples/stemi-robert-chen__ed-note.txt": "STEMI",
    "samples/dka-maria-gonzalez__ed-note.txt": "DKA",
    "samples/stroke-dorothy-williams__ed-note.txt": "Acute ischemic stroke",
}


@pytest.mark.parametrize("path,flag", HIGH.items())
def test_sample_triggers_expected_high_flag(path, flag):
    text = open(os.path.join(ROOT, path)).read()
    flags = _deterministic_flags(text, _fallback_extract_medications(text))
    assert {"flag": flag, "severity": "HIGH"}.items() <= next(f for f in flags if f["flag"] == flag).items()


def test_precision_and_recall_are_one_on_labeled_set():
    assert all(s["fn"] == 0 and s["fp"] == 0 for s in evaluate(LABELS).values())


def test_negative_charts_raise_no_flags():
    for path, expected in LABELS.items():
        if not expected:
            text = open(os.path.join(ROOT, path)).read()
            assert _deterministic_flags(text, []) == []


def test_nstemi_history_does_not_raise_stemi():
    text = open(os.path.join(ROOT, "samples/chf-jane-doe__ed-note.txt")).read()
    assert "STEMI" not in {f["flag"] for f in _deterministic_flags(text, [])}


@pytest.mark.parametrize("text,flag,expected", [
    ("Patient has DKA.", "DKA", "HIGH"),
    ("No DKA on labs.", "DKA", None),
    ("DKA was ruled out.", "DKA", None),
    ("Denies stroke alert criteria.", "Acute ischemic stroke", None),
    ("Rule out DKA. Awaiting ketones.", "DKA", "MEDIUM"),
    ("R/O STEMI, troponin pending.", "STEMI", "MEDIUM"),
    ("No chest pain. STEMI activated.", "STEMI", "HIGH"),
    ("No acute distress\nDKA confirmed", "DKA", "HIGH"),
    ("Not DKA. Later: DKA developed.", "DKA", "HIGH"),
    ("Discharge with outpatient follow up.", "Acute ischemic stroke", None),
])
def test_negation_and_rule_out(text, flag, expected):
    severity = {f["flag"]: f["severity"] for f in _deterministic_flags(text, [])}.get(flag)
    assert severity == expected
