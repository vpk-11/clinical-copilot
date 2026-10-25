"""
Parallel vs sequential pipeline latency, live LLM calls.
Usage: python scripts/bench_pipeline.py [runs=5]
Both modes call the same agent functions; sequential runs medication then timeline.
Cost: 5 charts x runs x 2 modes live pipeline runs.
"""
import glob
import os
import statistics
import sys
import time
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from agents import ingestion, medication, risk, synthesis, timeline
from orchestrator.pipeline import run_pipeline

SLEEP_S = 5


def run_sequential(text: str) -> None:
    trace_id = str(uuid.uuid4())
    ing = ingestion.run(text, "BENCH")
    med = medication.run(ing, trace_id)
    tl = timeline.run(ing, trace_id)
    risk_msg = risk.run(ing, med, trace_id)
    synthesis.run(ing, med, tl, risk_msg, trace_id)


def timed(fn, text: str) -> float:
    t0 = time.perf_counter()
    fn(text)
    return time.perf_counter() - t0


def p95(xs: list[float]) -> float:
    return sorted(xs)[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))]


def main() -> None:
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    modes = {"parallel": run_pipeline, "sequential": run_sequential}
    all_times: dict[str, list[float]] = {m: [] for m in modes}
    print(f"model={os.getenv('LLM_MODEL', 'default')} runs={runs}")
    for path in sorted(glob.glob(os.path.join(ROOT, "samples/*__ed-note.txt"))):
        text = open(path).read()
        name = os.path.basename(path).split("__")[0]
        for mode, fn in modes.items():
            times = []
            for _ in range(runs):
                times.append(timed(fn, text))
                time.sleep(SLEEP_S)
            all_times[mode] += times
            print(f"{name:28} {mode:10} median={statistics.median(times):6.2f}s p95={p95(times):6.2f}s")
    for mode, times in all_times.items():
        print(f"{'ALL':28} {mode:10} median={statistics.median(times):6.2f}s p95={p95(times):6.2f}s")


if __name__ == "__main__":
    main()
