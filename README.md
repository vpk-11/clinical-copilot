# ClinicalCopilot

<!-- version: v1.1.1 -->
![Version](https://img.shields.io/badge/version-v1.1.1-blue)

Multi-agent clinical chart analyzer. Paste a raw patient note and get a structured SOAP note, prioritized red flags, medication reconciliation with drug interaction alerts, and a reconstructed medical timeline.

> **Demo only.** Do not use with real patient data. Clinical text is sent to third-party LLM and tracing services (Anthropic, W&B Weave). No PHI redaction is applied.

**🚀 Live Demo:** [clinical-copilot-v5qq.onrender.com](https://clinical-copilot-v5qq.onrender.com/)

**📹 Demo Recording:** [Watch here](https://drive.google.com/file/d/1O5VG0oMqfU5h_XWtX1KQuSq83G04O8Xy/view?usp=sharing)

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
        |                           |
        v                           |
    RiskAgent                       |
  (deterministic + LLM)             |
        |                           |
        +---------------------------+
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

Medication and Timeline run in parallel. Risk waits on Medication. Synthesis collects all four.

Every agent returns `status="ok"` or `status="degraded"` so the API response distinguishes clean runs from fallback runs.

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI 0.136, Python 3.12 |
| LLM | LiteLLM 1.86 (provider-agnostic, swap via `LLM_MODEL` env var) |
| Frontend | React 19, Vite 8, TypeScript 6, Tailwind CSS 4 |
| Tracing | W&B Weave (best-effort, non-blocking) |
| Drug interactions | OpenFDA Drug Label API (no key required) |

---

## Setup

### Backend

```bash
conda create -n clinical-copilot python=3.12
conda activate clinical-copilot
pip install -r requirements.txt
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY and WANDB_API_KEY at minimum
python -m api.main
```

Runs on `PORT` from `.env` (default `8000`). If `WANDB_API_KEY` is missing, the server starts in degraded mode (no tracing, no crash). If `ANTHROPIC_API_KEY` is missing, LLM agents fall back to deterministic extraction.

### Frontend

```bash
cd client
pnpm install
pnpm dev   # dev server on CLIENT_PORT from .env (default 5173), proxies to PORT (default 8000)
```

Build for production:

```bash
cd client
pnpm build   # outputs to client/dist/, served by FastAPI at /
```

### Authentication

Set `API_KEY` in `.env` to enforce API key auth on all endpoints. Clients must send `X-API-Key: <your-key>` on every request. Leave unset to disable (local dev).

---

## Environment Variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | For Anthropic models | none | Provider key for default LiteLLM model |
| `WANDB_API_KEY` | No | none | W&B/Weave tracing. Missing = degraded mode |
| `WANDB_ENABLED` | No | `true` | Set to `false` to disable W&B/Weave entirely, regardless of whether `WANDB_API_KEY` is set |
| `LLM_MODEL` | No | `anthropic/claude-sonnet-4-20250514` | Any LiteLLM model string |
| `API_KEY` | No | none | Enables `X-API-Key` header enforcement |
| `ALLOWED_ORIGINS` | No | `http://localhost:5173` | Comma-separated CORS origin list |
| `WANDB_PROJECT` | No | `clinical-copilot` | W&B project name |
| `WANDB_ENTITY` | No | none | W&B username or org |
| `VITE_API_BASE_URL` | No | `` (same-origin) | Frontend backend base URL |
| `PORT` | No | `8000` | Backend port. Render sets this itself in production. |
| `CLIENT_PORT` | No | `5173` | Frontend dev server port (`pnpm dev` only, irrelevant to the production build). |

---

## LLM Provider

All agents call `shared/llm.py`. Swap providers by setting `LLM_MODEL` — no agent code changes:

```bash
LLM_MODEL=anthropic/claude-sonnet-4-20250514   # default
LLM_MODEL=openai/gpt-4o
LLM_MODEL=groq/llama-3.3-70b-versatile
LLM_MODEL=ollama/llama3
```

The matching provider SDK must be installed and the correct API key must be set. The `anthropic` package is already in `requirements.txt` for the default model.

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/upload` | Upload PDF, DOCX, MD, or TXT. Returns extracted text. |
| POST | `/normalize` | Normalize raw chart text via InputAgent. |
| POST | `/analyze` | Full pipeline. Returns SOAP note, flags, meds, timeline. Rate limited to 10/minute per IP. |
| GET | `/health` | Health check. No auth required. |
| GET | `/samples` | List sample patient bundles (synthetic data), grouped with demo ID, patient name, and file list. No auth required. |
| GET | `/samples/{filename}` | Download a single sample file (`.txt`/`.md`/`.pdf`/`.docx`). No auth required. |
| GET | `/samples/zip/{group}` | Download a whole patient's document bundle as a `.zip`. No auth required. |

All endpoints except `/health`, `/`, and `/samples*` require `X-API-Key` when `API_KEY` is set.

### Bring your own key

Every request to `/normalize` and `/analyze` can override the server's default LLM provider/model/key via headers, read once per request and never logged or persisted:

| Header | Purpose |
|---|---|
| `x-llm-provider` | `anthropic` \| `openai` \| `groq` \| `ollama`. Omit to use the server default entirely. |
| `x-llm-model` | Bare model id (e.g. `gpt-4o`). Blank falls back to that provider's default model. |
| `x-anthropic-api-key` / `x-openai-api-key` / `x-groq-api-key` | Caller-supplied key for the selected provider. Blank falls back to the server's env-configured key. |

The UI exposes this as a settings panel (top-right gear icon): keys are held in `sessionStorage`, sent as request headers, cleared when the tab closes, and cleared automatically if you switch provider (a key typed for one provider is meaningless for another).

`ollama` is rejected with a 400 on any hosted deployment (detected via Render's own `RENDER` env var) since it requires a server running on the same machine as the backend, which is never true on a hosted container. It only works when you run ClinicalCopilot locally with Ollama installed.

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
  "weave_url": "https://wandb.ai/...",
  "model_used": "anthropic/claude-sonnet-4-20250514",
  "used_byok": false
}
```

`pipeline_status` is `"ok"` on clean runs and `"degraded"` when any LLM step fell back to deterministic extraction. The response still contains usable data in degraded mode. `model_used` and `used_byok` tell you exactly which model ran and whether it was your pasted key or the server default. The UI shows all of this as a status strip above the results, plus a toast if the run degraded or failed outright.

---

## Sample Data

`samples/` holds synthetic patient bundles for demoing without real data. Files are named
`{group}__{document}.{ext}` — one group per patient, files vary in count and format per
group (2 to 4 files each: `.txt`, `.md`, `.pdf`, `.docx`) to mimic how real charts arrive
as a mismatched pile of documents rather than one clean file.

Every file in a group carries that patient's **Demo ID** (e.g. `DEMO-CHF-01`) so whichever
document gets opened first still tells you what to type into the app's Patient ID field.
The UI's sample picker shows the Demo ID, a copy button, per-file downloads, and a
"Download all" zip per patient.

To regenerate or edit sample content: `pip install -r requirements-dev.txt`, then edit and
rerun `python scripts/generate_samples.py`. Not a runtime dependency of the app.

## Pipeline Smoke Test

```bash
conda activate clinical-copilot
python -c "
from orchestrator.pipeline import run_pipeline
import json
result = run_pipeline(open('samples/chf-jane-doe__ed-note.txt').read())
print(json.dumps(result, indent=2))
"
```

---

## Project Structure

```
clinical-copilot/
├── agents/
│   ├── ingestion.py       <- section chunking, no LLM
│   ├── input.py           <- pre-analysis text normalization (LLM + fallback)
│   ├── medication.py      <- LiteLLM extraction + OpenFDA lookup
│   ├── timeline.py        <- chronological event extraction
│   ├── risk.py            <- deterministic thresholds + LLM flags
│   └── synthesis.py       <- SOAP note synthesis
├── orchestrator/
│   └── pipeline.py        <- parallel fan-out orchestration
├── api/
│   ├── main.py            <- FastAPI app, auth middleware, CORS, endpoints
│   └── limiter.py         <- slowapi rate limiter instance
├── shared/
│   ├── llm.py             <- LiteLLM wrapper, single LLM entry point
│   ├── models.py          <- AgentMessage TypedDict contract
│   ├── parser.py          <- PDF/DOCX/TXT/MD text extraction
│   └── reports.py         <- doctor + patient markdown report generation
├── weave_integration/
│   └── tracer.py          <- W&B Weave init and agent trace decorators
├── client/                <- React 19 + Vite 8 frontend (pnpm)
│   ├── src/
│   │   ├── App.tsx                    <- page state machine
│   │   ├── api.ts                     <- fetch wrappers
│   │   ├── types.ts                   <- shared TypeScript types
│   │   ├── hooks/
│   │   │   ├── useSession.ts          <- sessionStorage-backed state (BYOK config)
│   │   │   └── useToast.ts            <- transient toast queue (errors, degraded runs)
│   │   └── components/
│   │       ├── FileUpload.tsx         <- file intake + normalization + sample downloads
│   │       ├── ResultsDashboard.tsx   <- flags, reports, meds, timeline, model/key status strip
│   │       ├── ReportPanel.tsx        <- markdown render + print-to-PDF
│   │       ├── FlagBadge.tsx          <- severity badge
│   │       ├── SettingsPanel.tsx      <- BYOK provider/model/key panel
│   │       └── ToastStack.tsx         <- bottom-right toast notifications
│   └── vite.config.ts
├── samples/               <- synthetic patient document bundles, downloadable from the UI
├── scripts/
│   └── generate_samples.py <- authors samples/ content (needs requirements-dev.txt)
├── tests/                 <- pipeline test runner (samples/ has the fixtures)
├── .env.example
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

---

## Changelog
- **v1.1.1** (2026-07-19) — patch bump
- **v1.1.0** (2026-07-19) — live demo deployed on Render. Fixed BYOK key leaking across provider switches, blocked Ollama on hosted deploys, added model/key/degraded status strip and toast notifications to the results UI, added real application logging (was silently disabled), fixed static asset auth exemption.
