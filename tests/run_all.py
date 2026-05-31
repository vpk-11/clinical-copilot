"""
End-to-end test runner for all patient cases.
Usage: python tests/run_all.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from agents.ingestion import run as ing
from agents.medication import run as med
from agents.timeline import run as tl
from agents.risk import run as risk
from agents.synthesis import run as synth

CASES = [
    ("case_01_chf",    "tests/sample_chart.txt"),
    ("case_02_sepsis", "tests/case_02_sepsis.txt"),
    ("case_03_stemi",  "tests/case_03_stemi.txt"),
    ("case_04_dka",    "tests/case_04_dka.txt"),
    ("case_05_stroke", "tests/case_05_stroke.txt"),
]

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def check(label, condition):
    status = PASS if condition else FAIL
    print(f"    {status}  {label}")
    return condition


def run_case(name, path):
    print(f"\n{'='*55}")
    print(f"  {name.upper()}")
    print(f"{'='*55}")
    start = time.time()
    passed = 0
    total = 0

    try:
        text = open(path).read()

        i = ing(text)
        m = med(i, "test")
        t = tl(i, "test")
        r = risk(i, m, "test")
        s = synth(i, m, t, r, "test")

        elapsed = round(time.time() - start, 1)
        print(f"  Completed in {elapsed}s\n")

        # Ingestion
        chunks = i["payload"]["chunks"]
        total += 1; passed += check(f"Ingestion: {len(chunks)} chunks", len(chunks) >= 4)

        # Medications
        meds = m["payload"]["medications"]
        total += 1; passed += check(f"Medications: {len(meds)} extracted", len(meds) >= 1)
        total += 1; passed += check("No parse errors in meds", not any("parse_error" in x.get("name","") for x in meds))

        # Timeline
        events = t["payload"]["events"]
        total += 1; passed += check(f"Timeline: {len(events)} events", len(events) >= 1)

        # Risk flags
        flags = r["payload"]["flags"]
        high_flags = [f for f in flags if f.get("severity") == "HIGH"]
        total += 1; passed += check(f"Risk: {len(flags)} flags ({len(high_flags)} HIGH)", len(high_flags) >= 1)

        # Synthesis
        soap = s["payload"].get("soap_note", {})
        total += 1; passed += check("SOAP subjective populated", bool(soap.get("subjective") and soap["subjective"] != "Error"))
        total += 1; passed += check("SOAP assessment populated", bool(soap.get("assessment") and soap["assessment"] != "Error"))
        total += 1; passed += check("SOAP plan populated",       bool(soap.get("plan")       and soap["plan"]       != "Error"))
        total += 1; passed += check("Summary populated",         bool(s["payload"].get("summary") and s["payload"]["summary"] != "Synthesis failed"))

        print(f"\n  Red flags: {[f['flag'] for f in high_flags]}")
        print(f"  Medications: {[x['name'] for x in meds]}")

    except Exception as e:
        print(f"  \033[91mCRASHED: {e}\033[0m")

    print(f"\n  Result: {passed}/{total} checks passed")
    return passed, total


if __name__ == "__main__":
    total_passed = 0
    total_checks = 0

    for idx, (name, path) in enumerate(CASES):
        p, t = run_case(name, path)
        total_passed += p
        total_checks += t
        if idx < len(CASES) - 1:
            time.sleep(2)  # avoid Groq rate limits between cases

    print(f"\n{'='*55}")
    print(f"  TOTAL: {total_passed}/{total_checks} checks passed across {len(CASES)} cases")
    print(f"{'='*55}\n")

    if total_passed < total_checks:
        sys.exit(1)
