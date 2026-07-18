"""
End-to-end test runner for all patient cases.
Usage: python tests/run_all.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from weave_integration.tracer import init_weave
init_weave()

try:
    import wandb as _wandb
    _WANDB_AVAILABLE = True
except ImportError:
    _WANDB_AVAILABLE = False

from agents.ingestion import run as ing
from agents.medication import run as med
from agents.timeline import run as tl
from agents.risk import run as risk
from agents.synthesis import run as synth

CASES = [
    ("case_01_chf",    "samples/chf-jane-doe__ed-note.txt"),
    ("case_02_sepsis", "samples/sepsis-john-smith__ed-note.txt"),
    ("case_03_stemi",  "samples/stemi-robert-chen__ed-note.txt"),
    ("case_04_dka",    "samples/dka-maria-gonzalez__ed-note.txt"),
    ("case_05_stroke", "samples/stroke-dorothy-williams__ed-note.txt"),
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
    elapsed = 0.0
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
        elapsed = round(time.time() - start, 1)
        print(f"  \033[91mCRASHED: {e}\033[0m")

    print(f"\n  Result: {passed}/{total} checks passed")
    return passed, total, elapsed


if __name__ == "__main__":
    total_passed = 0
    total_checks = 0

    bench_table = None
    if _WANDB_AVAILABLE and _wandb.run is not None:
        bench_table = _wandb.Table(columns=["case", "passed", "total", "pass_rate", "latency_s"])

    for idx, (name, path) in enumerate(CASES):
        p, t, elapsed = run_case(name, path)
        total_passed += p
        total_checks += t

        if _WANDB_AVAILABLE and _wandb.run is not None:
            pass_rate = round(p / t, 3) if t else 0.0
            _wandb.log({
                f"benchmark/{name}/passed":   p,
                f"benchmark/{name}/total":    t,
                f"benchmark/{name}/pass_rate": pass_rate,
                f"benchmark/{name}/latency_s": elapsed,
            })
            if bench_table is not None:
                bench_table.add_data(name, p, t, pass_rate, elapsed)

        if idx < len(CASES) - 1:
            print(f"\n  Waiting 20s to avoid rate limits...")
            time.sleep(20)

    print(f"\n{'='*55}")
    print(f"  TOTAL: {total_passed}/{total_checks} checks passed across {len(CASES)} cases")
    print(f"{'='*55}\n")

    if _WANDB_AVAILABLE and _wandb.run is not None:
        overall_pass_rate = round(total_passed / total_checks, 3) if total_checks else 0.0
        _wandb.log({
            "benchmark/total_passed":   total_passed,
            "benchmark/total_checks":   total_checks,
            "benchmark/overall_pass_rate": overall_pass_rate,
        })
        if bench_table is not None:
            _wandb.log({"benchmark/results": bench_table})
        _wandb.finish()

    if total_passed < total_checks:
        sys.exit(1)
