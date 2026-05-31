import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from agents import ingestion, medication, timeline, risk, synthesis

try:
    from weave_integration.tracer import trace_agent
    ingestion.run  = trace_agent("ingestion")(ingestion.run)
    medication.run = trace_agent("medication")(medication.run)
    timeline.run   = trace_agent("timeline")(timeline.run)
    risk.run       = trace_agent("risk")(risk.run)
    synthesis.run  = trace_agent("synthesis")(synthesis.run)
    print("[pipeline] Weave tracing enabled")
except Exception as e:
    print(f"[pipeline] Weave not available, running without tracing: {e}")

_executor = ThreadPoolExecutor(max_workers=4)



def run_pipeline(raw_text: str, patient_id: str = "ANON") -> dict:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Called from within FastAPI's event loop — run in a fresh thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, _async_pipeline(raw_text, patient_id)).result()
    return asyncio.run(_async_pipeline(raw_text, patient_id))


async def _async_pipeline(raw_text: str, patient_id: str) -> dict:
    trace_id = str(uuid.uuid4())
    loop = asyncio.get_event_loop()

    ing = await loop.run_in_executor(_executor, ingestion.run, raw_text, patient_id)
    ing["trace_id"] = trace_id

    med_future = loop.run_in_executor(_executor, medication.run, ing, trace_id)
    tl_future  = loop.run_in_executor(_executor, timeline.run,   ing, trace_id)
    med, tl = await asyncio.gather(med_future, tl_future)

    risk_msg = await loop.run_in_executor(_executor, risk.run, ing, med, trace_id)

    synth = await loop.run_in_executor(
        _executor, synthesis.run, ing, med, tl, risk_msg, trace_id
    )

    return {
        "trace_id":        trace_id,
        "soap_note":       synth["payload"]["soap_note"],
        "red_flags":       synth["payload"]["red_flags"],
        "summary":         synth["payload"].get("summary", ""),
        "medications":     med["payload"]["medications"],
        "interactions":    med["payload"]["interactions"],
        "timeline_events": tl["payload"]["events"],
        "risk_flags":      risk_msg["payload"]["flags"],
    }
