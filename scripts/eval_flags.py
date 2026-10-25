"""
Precision/recall of agents.risk._deterministic_flags per flag family, no LLM.
Usage: python scripts/eval_flags.py
Exit 1 on any false negative or false positive (precision and recall gate at 1.0).
STEMI, Septic shock, DKA, Acute CHF decompensation and Acute ischemic stroke
are keyword rules on diagnosis text; the rest are numeric thresholds.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents.medication import _fallback_extract_medications
from agents.risk import _deterministic_flags


def evaluate(labels: dict) -> dict:
    stats: dict[str, dict] = {}
    for path, expected in labels.items():
        text = open(os.path.join(ROOT, path)).read()
        got = {f["flag"] for f in _deterministic_flags(text, _fallback_extract_medications(text))}
        for name in got | set(expected):
            s = stats.setdefault(name, {"tp": 0, "fp": 0, "fn": 0})
            if name in got and name in expected:
                s["tp"] += 1
            elif name in got:
                s["fp"] += 1
            else:
                s["fn"] += 1
    return stats


def main() -> int:
    labels = json.load(open(os.path.join(ROOT, "tests/eval/labels.json")))
    stats = evaluate(labels)
    print(f"{'flag':45} {'prec':>5} {'rec':>5}  tp fp fn")
    for name, s in sorted(stats.items()):
        prec = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else 1.0
        rec = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else 1.0
        print(f"{name:45} {prec:5.2f} {rec:5.2f}  {s['tp']:2} {s['fp']:2} {s['fn']:2}")
    return 1 if any(s["fn"] or s["fp"] for s in stats.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
