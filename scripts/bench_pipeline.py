"""
Parallel vs sequential pipeline latency, live LLM calls.
Usage: python scripts/bench_pipeline.py [runs=5] [sleep_s=30]
Both modes call the same agent functions; sequential runs medication then timeline.
Modes alternate within each repetition so provider drift hits both equally.
A run counts only if the pipeline status is ok and no rate-limit/timeout backoff
fired during it; other runs are reported separately, never averaged in.
Cost: 5 charts x runs x 2 modes live pipeline runs.
"""
import glob
import json
import os
import statistics
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import shared.llm as llm
from agents import ingestion, medication, risk, synthesis, timeline
from orchestrator.pipeline import run_pipeline

backoffs = [0]
_retry_delay = llm.retry_delay


def _counted_retry_delay(e, attempt):
    backoffs[0] += 1
    return _retry_delay(e, attempt)


llm.retry_delay = _counted_retry_delay


def run_parallel(text: str) -> str:
    return run_pipeline(text, "BENCH")["pipeline_status"]


def run_sequential(text: str) -> str:
    trace_id = str(uuid.uuid4())
    ing = ingestion.run(text, "BENCH")
    med = medication.run(ing, trace_id)
    tl = timeline.run(ing, trace_id)
    risk_msg = risk.run(ing, med, trace_id)
    synth = synthesis.run(ing, med, tl, risk_msg, trace_id)
    msgs = (med, tl, risk_msg, synth)
    return "ok" if all(m["status"] == "ok" for m in msgs) else "degraded"


MODES = {"parallel": run_parallel, "sequential": run_sequential}


def timed(fn, text: str) -> tuple[float, bool]:
    before = backoffs[0]
    t0 = time.perf_counter()
    status = fn(text)
    return time.perf_counter() - t0, status == "ok" and backoffs[0] == before


def p95(xs: list[float]) -> float:
    return sorted(xs)[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]


def summarize(label: str, mode: str, runs: list[tuple[float, bool]]) -> dict:
    clean = [t for t, ok in runs if ok]
    row = {"chart": label, "mode": mode, "clean": len(clean), "total": len(runs)}
    if clean:
        row.update(median_s=round(statistics.median(clean), 2), p95_s=round(p95(clean), 2))
    print(f"{label:28} {mode:10} clean={len(clean)}/{len(runs)} "
          + (f"median={row['median_s']:6.2f}s p95={row['p95_s']:6.2f}s" if clean else "no clean runs"), flush=True)
    return row


def main() -> None:
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    sleep_s = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    model = os.getenv("LLM_MODEL", llm.DEFAULT_MODEL)
    print(f"model={model} reps={reps} sleep={sleep_s}s", flush=True)
    results: dict[str, list[tuple[float, bool]]] = {m: [] for m in MODES}
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "samples/*__ed-note.txt"))):
        text = open(path).read()
        name = os.path.basename(path).split("__")[0]
        per_mode: dict[str, list[tuple[float, bool]]] = {m: [] for m in MODES}
        for _ in range(reps):
            for mode, fn in MODES.items():
                per_mode[mode].append(timed(fn, text))
                time.sleep(sleep_s)
        for mode, runs in per_mode.items():
            results[mode] += runs
            rows.append(summarize(name, mode, runs))
    for mode, runs in results.items():
        rows.append(summarize("ALL", mode, runs))
    out = os.path.join(ROOT, "scripts", "bench_results.json")
    json.dump({"model": model, "reps": reps, "sleep_s": sleep_s, "rows": rows}, open(out, "w"), indent=2)
    print(f"wrote {out}", flush=True)


if __name__ == "__main__":
    main()
