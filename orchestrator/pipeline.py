import asyncio
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from agents import ingestion, medication, timeline, risk, synthesis

try:
    from weave_integration.tracer import trace_agent, WANDB_ENABLED
    ingestion.run  = trace_agent("ingestion")(ingestion.run)
    medication.run = trace_agent("medication")(medication.run)
    timeline.run   = trace_agent("timeline")(timeline.run)
    risk.run       = trace_agent("risk")(risk.run)
    synthesis.run  = trace_agent("synthesis")(synthesis.run)
    print("[pipeline] Weave tracing enabled" if WANDB_ENABLED else "[pipeline] Weave tracing disabled (WANDB_ENABLED=false)")
except Exception as e:
    print(f"[pipeline] Weave not available, running without tracing: {e}")

_executor = ThreadPoolExecutor(max_workers=4)



def run_pipeline(
    raw_text: str,
    patient_id: str = "ANON",
    llm_config: dict | None = None,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Called from within FastAPI's event loop — run in a fresh thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, run_pipeline_async(raw_text, patient_id, llm_config, progress)).result()
    return asyncio.run(run_pipeline_async(raw_text, patient_id, llm_config, progress))


async def run_pipeline_async(
    raw_text: str,
    patient_id: str,
    llm_config: dict | None = None,
    progress: Callable[[dict], None] | None = None,
) -> dict:
    trace_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()

    async def step(name, fn, *args):
        if progress:
            progress({"event": "agent_started", "agent": name})
        msg = await loop.run_in_executor(_executor, fn, *args)
        if progress:
            progress({
                "event": "agent_finished",
                "agent": name,
                "status": msg["status"],
                "reason": msg["payload"].get("reason", ""),
            })
        return msg

    ing = await step("ingestion", ingestion.run, raw_text, patient_id)
    ing["trace_id"] = trace_id

    med, tl = await asyncio.gather(
        step("medication", medication.run, ing, trace_id, llm_config),
        step("timeline", timeline.run, ing, trace_id, llm_config),
    )
    risk_msg = await step("risk", risk.run, ing, med, trace_id, llm_config)
    synth = await step("synthesis", synthesis.run, ing, med, tl, risk_msg, trace_id, llm_config)

    degraded = [m for m in (med, tl, risk_msg, synth) if m["status"] != "ok"]
    status = "degraded" if degraded else "ok"
    reason = "; ".join(f"{m['agent']}: {m['payload'].get('reason', '')}" for m in degraded)

    return {
        "trace_id":              trace_id,
        "pipeline_status":       status,
        "pipeline_status_reason": reason,
        "soap_note":             synth["payload"]["soap_note"],
        "red_flags":             synth["payload"]["red_flags"],
        "summary":               synth["payload"].get("summary", ""),
        "medications":           med["payload"]["medications"],
        "interactions":          med["payload"]["interactions"],
        "timeline_events":       tl["payload"]["events"],
        "risk_flags":            risk_msg["payload"]["flags"],
    }
