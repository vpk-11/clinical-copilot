import logging
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

logger = logging.getLogger(__name__)

try:
    from weave_integration.tracer import init_weave
    init_weave()
except Exception as e:
    logger.warning("Weave init failed — tracing disabled: %s", e)

from orchestrator.pipeline import run_pipeline
from shared.parser import extract_text
from shared.reports import generate_doctor_report, generate_patient_report

app = FastAPI(title="ClinicalCopilot", version="2.0.0")

_API_KEY = os.environ.get("API_KEY")

# .doc is intentionally excluded — python-docx parses .docx (Office Open XML)
# but cannot parse binary .doc (Word 97-2003) format.
ALLOWED_EXTENSIONS = {"pdf", "docx", "md", "txt"}

_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]


@app.middleware("http")
async def api_key_middleware(request: Request, call_next):
    if _API_KEY and request.url.path not in ("/health", "/"):
        client_key = request.headers.get("X-API-Key")
        if client_key != _API_KEY:
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
async def normalize(req: NormalizeRequest):
    """Run InputAgent to normalize raw text into structured clinical chart format."""
    if not req.text or len(req.text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Text too short to normalize.")

    from agents.input import run as input_run
    result = input_run(req.text.strip(), req.patient_id)
    normalized = result["payload"]["normalized_text"]

    return NormalizeResponse(
        normalized_text=normalized,
        original_char_count=len(req.text),
        normalized_char_count=len(normalized),
        status=result["status"],
        status_reason=result["payload"].get("reason", ""),
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if not req.text or len(req.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short. Provide a clinical chart.")
    try:
        result = run_pipeline(req.text.strip(), req.patient_id)

        doctor_report = generate_doctor_report(result, req.patient_id)
        patient_report = generate_patient_report(result)

        entity = os.environ.get("WANDB_ENTITY", "")
        project = os.environ.get("WANDB_PROJECT", "clinical-copilot")
        weave_url = (
            f"https://wandb.ai/{entity}/{project}/weave"
            if entity
            else f"https://wandb.ai/{project}/weave"
        )

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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok", "service": "ClinicalCopilot", "version": "2.0.0"}


# Serve built React app — only mounted when dist/ exists
_dist = Path("ui/dist")
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="ui")
else:
    @app.get("/")
    def serve_ui():
        return FileResponse("ui/index.html")
