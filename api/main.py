import hmac
import io
import logging
import os
import zipfile
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.limiter import limiter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

try:
    from weave_integration.tracer import init_weave
    init_weave()
except Exception as e:
    logger.warning("Weave init failed — tracing disabled: %s", e)

from orchestrator.pipeline import run_pipeline
from shared.parser import extract_text
from shared.reports import generate_doctor_report, generate_patient_report
from shared.llm import DEFAULT_MODEL as _DEFAULT_LLM_MODEL

app = FastAPI(title="ClinicalCopilot", version="2.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_API_KEY = os.environ.get("API_KEY")

# Render sets this automatically on every service. Ollama needs a locally
# running server on the same machine as the backend process — that's never
# true on a hosted deploy, so refuse it there instead of failing deep
# inside litellm with a confusing connection error.
_IS_HOSTED = bool(os.environ.get("RENDER"))

# .doc is intentionally excluded — python-docx parses .docx (Office Open XML)
# but cannot parse binary .doc (Word 97-2003) format.
ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

_SAMPLES_DIR = Path(__file__).resolve().parent.parent / "samples"

# Sample files are named "{group}__{doc}.{ext}" — one group per synthetic
# patient, files vary in count/format per group to mirror how real charts
# arrive as a mismatched pile of documents. demo_id is what a demo-er types
# into the UI's Patient ID field; it's baked into each group's ed-note.txt too.
_SAMPLE_GROUPS = {
    "chf-jane-doe":            {"demo_id": "DEMO-CHF-01", "patient": "Jane Doe",       "label": "CHF"},
    "sepsis-john-smith":       {"demo_id": "DEMO-SEP-01", "patient": "John Smith",     "label": "Sepsis"},
    "stemi-robert-chen":       {"demo_id": "DEMO-MI-01",  "patient": "Robert Chen",    "label": "STEMI"},
    "dka-maria-gonzalez":      {"demo_id": "DEMO-DKA-01", "patient": "Maria Gonzalez", "label": "DKA"},
    "stroke-dorothy-williams": {"demo_id": "DEMO-CVA-01", "patient": "Dorothy Williams", "label": "Stroke"},
}

# BYOK — caller-supplied provider/model/key headers. Read per-request,
# never logged, never persisted. See _build_llm_config_from_headers.
_PROVIDER_KEY_HEADERS = {
    "anthropic": "x-anthropic-api-key",
    "openai": "x-openai-api-key",
    "groq": "x-groq-api-key",
}
_PROVIDER_DEFAULT_MODELS = {
    "anthropic": "anthropic/claude-sonnet-4-20250514",
    "openai": "openai/gpt-4o",
    "groq": "groq/llama-3.3-70b-versatile",
    "ollama": "ollama/llama3",
}


def _build_llm_config_from_headers(request: Request) -> dict | None:
    """
    x-llm-provider selects anthropic|openai|groq|ollama.
    x-llm-model is the bare model id (e.g. "gpt-4o"); blank falls back to
    that provider's default. x-<provider>-api-key supplies the caller's own
    key; blank falls back to the server's env-configured key for that
    provider. Returns None if no provider header is set (use server default
    model + server env keys, same as before BYOK existed).
    """
    provider = request.headers.get("x-llm-provider", "").strip().lower()
    if provider not in _PROVIDER_DEFAULT_MODELS:
        return None
    if provider == "ollama" and _IS_HOSTED:
        raise HTTPException(
            status_code=400,
            detail=(
                "Ollama requires a locally running server on the same machine as "
                "the backend. It isn't available on this hosted deployment — "
                "self-host ClinicalCopilot with Ollama running to use it."
            ),
        )
    model_name = request.headers.get("x-llm-model", "").strip()
    model = f"{provider}/{model_name}" if model_name else _PROVIDER_DEFAULT_MODELS[provider]
    key_header = _PROVIDER_KEY_HEADERS.get(provider)
    api_key = request.headers.get(key_header, "").strip() if key_header else ""
    return {"model": model, "api_key": api_key or None}


def _llm_meta(llm_config: dict | None) -> tuple[str, bool]:
    """Returns (model actually in use, whether a caller-supplied key was used)."""
    if llm_config:
        return llm_config["model"], bool(llm_config.get("api_key"))
    return os.environ.get("LLM_MODEL", _DEFAULT_LLM_MODEL), False


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    path = request.url.path
    exempt = (
        path in ("/health", "/", "/favicon.ico")
        or path.startswith("/samples")
        or path.startswith("/assets/")
    )
    if _API_KEY and not exempt:
        client_key = request.headers.get("X-API-Key", "")
        if not hmac.compare_digest(client_key, _API_KEY):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid API key. Set X-API-Key header."},
            )
    return await call_next(request)


# CORS must be added after the API key middleware so it wraps everything
# and adds CORS headers even to 401 responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NormalizeRequest(BaseModel):
    text: str
    patient_id: str = "DEMO-001"


class NormalizeResponse(BaseModel):
    normalized_text: str
    original_char_count: int
    normalized_char_count: int
    status: str = "ok"
    status_reason: str = ""
    model_used: str = ""
    used_byok: bool = False


class AnalyzeRequest(BaseModel):
    text: str
    patient_id: str = "DEMO-001"


class AnalyzeResponse(BaseModel):
    trace_id: str
    pipeline_status: str
    pipeline_status_reason: str
    doctor_report: str
    patient_report: str
    soap_note: dict
    red_flags: list
    summary: str
    medications: list
    interactions: list
    timeline_events: list
    risk_flags: list
    weave_url: str
    model_used: str
    used_byok: bool


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Extract text from an uploaded PDF, DOCX, MD, or TXT file."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 10 MB.")

    try:
        text = extract_text(file.filename, content)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract any text from this file.")

    return {
        "text": text,
        "filename": file.filename,
        "char_count": len(text),
    }


@app.post("/normalize", response_model=NormalizeResponse)
async def normalize(req: NormalizeRequest, request: Request):
    """Run InputAgent to normalize raw text into structured clinical chart format."""
    if not req.text or len(req.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Text too short to normalize.")

    llm_config = _build_llm_config_from_headers(request)
    model_used, used_byok = _llm_meta(llm_config)
    from agents.input import run as input_run
    result = input_run(req.text.strip(), req.patient_id, llm_config)
    normalized = result["payload"]["normalized_text"]

    logger.info(
        "normalize patient_id=%s model=%s byok=%s status=%s reason=%s chars=%d",
        req.patient_id, model_used, used_byok, result["status"],
        result["payload"].get("reason", ""), len(normalized),
    )

    return NormalizeResponse(
        normalized_text=normalized,
        original_char_count=len(req.text),
        normalized_char_count=len(normalized),
        status=result["status"],
        status_reason=result["payload"].get("reason", ""),
        model_used=model_used,
        used_byok=used_byok,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze(req: AnalyzeRequest, request: Request):
    if not req.text or len(req.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short. Provide a clinical chart.")
    llm_config = _build_llm_config_from_headers(request)
    model_used, used_byok = _llm_meta(llm_config)
    try:
        result = run_pipeline(req.text.strip(), req.patient_id, llm_config)

        doctor_report = generate_doctor_report(result, req.patient_id)
        patient_report = generate_patient_report(result)

        logger.info(
            "analyze patient_id=%s model=%s byok=%s pipeline_status=%s reason=%s "
            "flags=%d meds=%d trace_id=%s",
            req.patient_id, model_used, used_byok,
            result.get("pipeline_status", "ok"), result.get("pipeline_status_reason", ""),
            len(result["risk_flags"]), len(result["medications"]), result["trace_id"],
        )

        from weave_integration.tracer import WANDB_ENABLED
        if WANDB_ENABLED:
            entity = os.environ.get("WANDB_ENTITY", "")
            project = os.environ.get("WANDB_PROJECT", "clinical-copilot")
            weave_url = (
                f"https://wandb.ai/{entity}/{project}/weave"
                if entity
                else f"https://wandb.ai/{project}/weave"
            )
        else:
            weave_url = ""

        return AnalyzeResponse(
            trace_id=result["trace_id"],
            pipeline_status=result.get("pipeline_status", "ok"),
            pipeline_status_reason=result.get("pipeline_status_reason", ""),
            doctor_report=doctor_report,
            patient_report=patient_report,
            soap_note=result["soap_note"],
            red_flags=result["red_flags"],
            summary=result.get("summary", ""),
            medications=result["medications"],
            interactions=result["interactions"],
            timeline_events=result["timeline_events"],
            risk_flags=result["risk_flags"],
            weave_url=weave_url,
            model_used=model_used,
            used_byok=used_byok,
        )
    except Exception as e:
        logger.exception("analyze failed patient_id=%s model=%s byok=%s", req.patient_id, model_used, used_byok)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ClinicalCopilot", "version": "2.0.0"}


_SAMPLE_MEDIA_TYPES = {
    "txt": "text/plain",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _sample_group_of(filename: str) -> str | None:
    return filename.split("__", 1)[0] if "__" in filename else None


@app.get("/samples")
def list_samples():
    """
    List downloadable sample charts, grouped by synthetic patient — each
    group is a mismatched pile of documents (not all groups have the same
    file types) meant to be downloaded together and re-uploaded as a set.
    """
    if not _SAMPLES_DIR.exists():
        return {"groups": []}

    files_by_group: dict[str, list[str]] = {}
    for path in sorted(_SAMPLES_DIR.glob("*")):
        if not path.is_file():
            continue
        group = _sample_group_of(path.name)
        if group is None:
            continue
        files_by_group.setdefault(group, []).append(path.name)

    groups = []
    for group, files in sorted(files_by_group.items()):
        meta = _SAMPLE_GROUPS.get(group, {"demo_id": "", "patient": "", "label": group})
        groups.append({"group": group, "files": files, **meta})
    return {"groups": groups}


@app.get("/samples/{filename}")
def download_sample(filename: str):
    if "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _SAMPLE_MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    path = _SAMPLES_DIR / filename
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Sample not found.")
    return FileResponse(path, media_type=_SAMPLE_MEDIA_TYPES[ext], filename=filename)


@app.get("/samples/zip/{group}")
def download_sample_zip(group: str):
    if "/" in group or "\\" in group or group not in _SAMPLE_GROUPS:
        raise HTTPException(status_code=404, detail="Sample group not found.")
    files = sorted(_SAMPLES_DIR.glob(f"{group}__*"))
    if not files:
        raise HTTPException(status_code=404, detail="Sample group not found.")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            zf.write(path, arcname=path.name)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{group}.zip"'},
    )


# Serve built React app — only mounted when dist/ exists
_dist = Path("client/dist")
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="client")
else:
    @app.get("/")
    def serve_ui():
        return FileResponse("client/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=True)
