# ClinicalCopilot

Multi-agent clinical chart analyzer. Paste a raw patient note and get a structured SOAP note, prioritized red flags, medication reconciliation with drug interaction alerts, and a reconstructed medical timeline.

> **Demo only.** Do not use with real patient data. Clinical text is sent to third-party LLM and tracing services (Anthropic, W&B Weave). No PHI redaction is applied.

---

## What It Does

- **SOAP note** structured from unstructured chart text
- **Red flags** ranked by severity (HIGH / MEDIUM / LOW) using deterministic clinical thresholds plus LLM extraction
- **Medication list** with OpenFDA drug interaction alerts
- **Medical timeline** reconstructed from chart history
- **W&B Weave trace** of every agent call for auditability

## Architecture

```
[Raw Clinical Text]
        |
        v
  IngestionAgent        <- cleans + chunks input (no LLM, pure Python)
        |
        +---------------------------+
        v                           v
  MedicationAgent           TimelineAgent
  (LiteLLM + OpenFDA)       (LiteLLM)
        |
        v
    RiskAgent             <- deterministic threshold checks + LLM flags
  (LiteLLM)
        |
        v  (all 4 results collected)
  SynthesisAgent          <- merges into SOAP note + summary
  (LiteLLM)
        |
        v
  FastAPI /analyze
        |
        v
  React UI  +  W&B Weave Dashboard
```

Medication and Timeline run in parallel. Risk waits on Medication. Synthesis waits on all four.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI, Python 3.11 |
| LLM | LiteLLM (provider-agnostic — swap via env var) |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Tracing | W&B Weave |
| Drug interactions | OpenFDA Drug Label API (no key required) |

---

## Setup

### Backend

```bash
conda create -n clinical-copilot python=3.12
conda activate clinical-copilot
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY and WANDB_API_KEY at minimum
uvicorn api.main:app --reload --port 8000
```

If `WANDB_API_KEY` is missing, the server starts in degraded mode (no tracing). If `ANTHROPIC_API_KEY` is missing, LLM agents fall back to deterministic extraction.

### Frontend

```bash
cd client
pnpm install
pnpm dev   # dev server on :5173 with proxy to :8000
```

Build for production:

```bash
cd client
pnpm build   # outputs to client/dist/ — served by FastAPI at /
```

### Authentication

Set `API_KEY` in `.env` to enable API key enforcement on all endpoints. Clients must send `X-API-Key: <your-key>` on every request. Leave unset to disable auth (local dev).

---

## LLM Provider

All agents call `shared/llm.py`. Swap providers by setting `LLM_MODEL` — no agent code changes:

```bash
LLM_MODEL=anthropic/claude-sonnet-4-20250514   # default
LLM_MODEL=openai/gpt-4o
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_MODEL=ollama/llama3
```

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload PDF, DOCX, MD, or TXT. Returns extracted text. |
| POST | `/normalize` | Normalize raw chart text via InputAgent. |
| POST | `/analyze` | Full pipeline. Returns SOAP note, flags, meds, timeline. |
| GET | `/health` | Health check. |

### `/analyze` response

```json
{
  "trace_id": "uuid",
  "pipeline_status": "ok",
  "pipeline_status_reason": "",
  "soap_note": { "subjective": "", "objective": "", "assessment": "", "plan": "" },
  "red_flags": ["K+ 6.1 CRITICAL", "SpO2 91% on RA"],
  "summary": "...",
  "medications": [{ "name": "", "dose": "", "frequency": "" }],
  "interactions": [{ "drug": "", "warnings": "" }],
  "timeline_events": [{ "date": "", "event": "", "category": "" }],
  "risk_flags": [{ "flag": "", "severity": "HIGH", "evidence": "" }],
  "weave_url": "https://wandb.ai/..."
}
```

`pipeline_status` is `"ok"` on clean runs and `"degraded"` when any LLM step fell back to deterministic extraction. The response still contains useful data in degraded mode.

---

## Pipeline Smoke Test

```bash
conda activate clinical-copilot
python -c "
from orchestrator.pipeline import run_pipeline
import json
result = run_pipeline(open('tests/sample_chart.txt').read())
print(json.dumps(result, indent=2))
"
```

---

## Project Structure

```
clinical-copilot/
├── agents/
│   ├── ingestion.py       <- section chunking, no LLM
│   ├── input.py           <- pre-analysis text normalization
│   ├── medication.py      <- LiteLLM extraction + OpenFDA lookup
│   ├── timeline.py        <- chronological event extraction
│   ├── risk.py            <- deterministic thresholds + LLM flags
│   └── synthesis.py       <- SOAP note synthesis
├── orchestrator/
│   └── pipeline.py        <- parallel fan-out orchestration
├── api/
│   └── main.py            <- FastAPI app, endpoints, auth middleware
├── shared/
│   ├── llm.py             <- LiteLLM wrapper, single LLM entry point
│   ├── models.py          <- AgentMessage TypedDict contract
│   ├── parser.py          <- PDF/DOCX/TXT text extraction
│   └── reports.py         <- doctor + patient markdown report generation
├── weave_integration/
│   └── tracer.py          <- W&B Weave init and agent trace decorators
├── client/                <- React + Vite frontend
├── tests/                 <- synthetic clinical test cases
├── .env.example
├── requirements.txt
└── README.md
```
