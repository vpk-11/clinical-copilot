# ClinicalCopilot

> Transforms unstructured medical charts into structured SOAP notes with red flag detection.
> Built at AGI House × W&B Multi-Agent Orchestration Build Day — May 31, 2026

---

## What It Does

Paste a raw clinical chart and get back:

- A structured **SOAP note** (Subjective / Objective / Assessment / Plan)
- Prioritized **red flags** (critical vitals, dangerous lab values, acute diagnoses)
- **Medication list** with drug interaction alerts via OpenFDA
- **Chronological medical timeline** reconstructed from notes
- **W&B Weave audit trail** of every agent decision

---

## Architecture

```
[Raw Clinical Text]
        │
        ▼
  IngestionAgent          ← cleans + chunks input (no LLM)
        │
        ├──────────────────────────────┐
        ▼                              ▼
  MedicationAgent              TimelineAgent
  (LiteLLM + OpenFDA)          (LiteLLM)
        │
        ▼
    RiskAgent                  ← needs medication output
  (LiteLLM, clinical thresholds)
        │
        ▼ (all 4 results collected)
  SynthesisAgent               ← merges everything into SOAP note
  (LiteLLM)
        │
        ▼
  [FastAPI /analyze endpoint]
        │
        ▼
  [UI: index.html]   +   [W&B Weave Dashboard]
```

**Medication + Timeline run in parallel (asyncio). Risk waits for Medication. Synthesis waits for all 4.**

---

## LLM Layer — LiteLLM (Provider-Agnostic)

All LLM calls go through `shared/llm.py`. Swap models by changing **one env var** — no agent code changes needed.

```bash
# Default
LLM_MODEL=anthropic/claude-sonnet-4-20250514

# OpenAI
LLM_MODEL=openai/gpt-4o

# Groq (fast, free tier)
LLM_MODEL=groq/llama-3.1-70b-versatile

# Local
LLM_MODEL=ollama/llama3
```

---

## Repo Structure

```
clinical-copilot/
├── shared/
│   ├── __init__.py
│   ├── models.py              ← AgentMessage contract — DO NOT CHANGE without team agreement
│   └── llm.py                 ← LiteLLM wrapper — single place for LLM config
├── agents/
│   ├── __init__.py
│   ├── ingestion.py           ← Person 1 (verify + tune)
│   ├── medication.py          ← Person 1 (verify + tune)
│   ├── timeline.py            ← Person 1 (verify + tune)
│   ├── risk.py                ← Person 1 (verify + tune — most important)
│   └── synthesis.py           ← Person 3 (verify + tune)
├── orchestrator/
│   ├── __init__.py
│   └── pipeline.py            ← Person 3 (verify)
├── api/
│   ├── __init__.py
│   └── main.py                ← Person 2
├── ui/
│   └── index.html             ← Person 2
├── weave_integration/
│   ├── __init__.py
│   └── tracer.py              ← Person 2
├── tests/
│   └── sample_chart.txt       ← Person 3 (push immediately)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Shared Message Contract

**Every agent input and output uses this exact TypedDict. Do not deviate.**

```python
# shared/models.py
from typing import TypedDict

class AgentMessage(TypedDict):
    agent: str        # "ingestion" | "medication" | "timeline" | "risk" | "synthesis"
    status: str       # "ok" | "error"
    payload: dict     # agent-specific (see schemas below)
    trace_id: str     # UUID4 — same value for entire pipeline run
    timestamp: str    # ISO 8601 UTC
```

### Payload Schemas

| Agent | Payload Keys |
|---|---|
| ingestion | `chunks: List[str]`, `raw_text: str`, `patient_id: str` |
| medication | `medications: List[{name, dose, frequency}]`, `interactions: List[{drug, warnings}]` |
| timeline | `events: List[{date, event, category}]` |
| risk | `flags: List[{flag, severity: HIGH\|MEDIUM\|LOW, evidence}]` |
| synthesis | `soap_note: {subjective, objective, assessment, plan}`, `summary: str`, `red_flags: List[str]` |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/analyze` | Main pipeline. Body: `{text: str, patient_id: str}` |
| GET | `/health` | Health check |

### Response shape

```json
{
  "trace_id": "uuid",
  "soap_note": { "subjective": "", "objective": "", "assessment": "", "plan": "" },
  "red_flags": ["K+ 6.1 CRITICAL", "SpO2 91% on RA"],
  "summary": "One-sentence executive summary",
  "medications": [{ "name": "", "dose": "", "frequency": "" }],
  "interactions": [{ "drug": "", "warnings": "" }],
  "timeline_events": [{ "date": "", "event": "", "category": "" }],
  "risk_flags": [{ "flag": "", "severity": "HIGH", "evidence": "" }],
  "weave_url": "https://wandb.ai/..."
}
```

---

## External APIs Used

| API | Purpose | Auth |
|---|---|---|
| LiteLLM (any provider) | All 4 LLM agents — set `LLM_MODEL` in `.env` | Provider key (e.g. `ANTHROPIC_API_KEY`) |
| OpenFDA Drug Label API | Drug interaction detection | None (free, no key) |
| W&B Weave | Agent call tracing + audit trail | `WANDB_API_KEY` |

OpenFDA endpoint: `https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug}&limit=1`

---

## Environment Setup

```bash
git clone https://github.com/SIDEYS/clinical-copilot
cd clinical-copilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, WANDB_API_KEY, WANDB_ENTITY in .env
uvicorn api.main:app --reload --port 8000
# Open ui/index.html in browser
```

### .env.example

```
ANTHROPIC_API_KEY=your_anthropic_key_here
WANDB_API_KEY=your_wandb_key_here
WANDB_PROJECT=clinical-copilot
WANDB_ENTITY=your_wandb_username_here

# Change this one line to swap LLM providers — no code changes needed
LLM_MODEL=anthropic/claude-sonnet-4-20250514
```

---

## Running the Pipeline Directly

```bash
python -c "
from orchestrator.pipeline import run_pipeline
result = run_pipeline(open('tests/sample_chart.txt').read())
import json; print(json.dumps(result, indent=2))
"
```

---

## W&B Weave

Every agent call is wrapped with a `@weave.op` decorator. The Weave dashboard shows:
- Input/output for each of the 5 agents
- Latency per agent
- Token usage per LLM call
- Full trace graph showing the parallel fan-out

**Weave Dashboard:** https://wandb.ai/abhale-university-of-massachusetts/clinical-copilot/weave

---

## Hackathon Submission

- **Event:** AGI House × W&B Multi-Agent Orchestration Build Day
- **Submission URL:** app.agihouse.org/events/multi-agent-orchestration-build-day
- **Draft due:** 7:00 PM
- **Final due:** 8:00 PM
- **Demo:** 3-minute live presentation + Q&A

### Judging Criteria Coverage

| Criterion | How We Satisfy It |
|---|---|
| Agent Orchestration | 5 agents, parallel asyncio fan-out, typed AgentMessage contract |
| Utility | Real clinical pain point — 2+ hrs/day saved on documentation |
| Technical Execution | FastAPI, LiteLLM (modular), typed contracts, OpenFDA, error handling |
| Creativity | Parallel specialist agents + full auditability for clinical AI |
| Sponsor Tool Usage | W&B Weave traces every agent call — also targeting Best Use of Weave ($1k) |

---

## Team

| Role | Responsibility |
|---|---|
| Person 1 — ML Engineer | Validate + tune IngestionAgent, MedicationAgent, TimelineAgent, RiskAgent |
| Person 2 — Infra Engineer | shared/models.py, shared/llm.py, FastAPI, Weave integration, UI |
| Person 3 — Pipeline Lead | Validate SynthesisAgent + Orchestrator, sample data, demo + submission |

---

## Timeline

| Time | Milestone |
|---|---|
| 0:00–0:20 | Person 3 pushes sample_chart.txt. Unblocks Person 1. |
| 0:20–1:30 | Person 1 tunes agents, Person 2 sets up W&B, Person 3 validates pipeline |
| 1:30–1:45 | Integration checkpoint 1 — full pipeline runs end-to-end |
| 1:45–3:00 | API + UI working, Weave traces showing |
| 3:00–3:30 | Weave dashboard polish, UI polish |
| 3:30–4:00 | Demo prep + rehearsal |
| 4:00–4:20 | Record 2-min screen demo |
| 4:20–4:30 | Submit on AGI House platform |
