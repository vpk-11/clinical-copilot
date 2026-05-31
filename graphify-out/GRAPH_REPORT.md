# Graph Report - clinicalcopilot  (2026-05-31)

## Corpus Check
- 19 files · ~5,321 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 138 nodes · 144 edges · 16 communities (13 shown, 3 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6251d465`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Weave Tracing Integration|Weave Tracing Integration]]
- [[_COMMUNITY_Multi-Agent Pipeline|Multi-Agent Pipeline]]
- [[_COMMUNITY_FastAPI Endpoints|FastAPI Endpoints]]
- [[_COMMUNITY_Orchestration Pipeline|Orchestration Pipeline]]
- [[_COMMUNITY_UI-API Bridge|UI-API Bridge]]
- [[_COMMUNITY_Shared Data Models|Shared Data Models]]
- [[_COMMUNITY_Health Check|Health Check]]
- [[_COMMUNITY_FastAPI App|FastAPI App]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]

## God Nodes (most connected - your core abstractions)
1. `ClinicalCopilot 🏥` - 14 edges
2. `ClinicalCopilot — Person 3 Task Sheet` - 13 edges
3. `ClinicalCopilot — Person 1 Task Sheet` - 13 edges
4. `AgentMessage` - 10 edges
5. `run_pipeline()` - 9 edges
6. `trace_agent()` - 5 edges
7. `chat()` - 5 edges
8. `AnalyzeResponse` - 5 edges
9. `IngestionAgent` - 5 edges
10. `init_weave()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `AnalyzeResponse` --shares_data_with--> `renderResults() JS function`  [INFERRED]
  api/main.py → ui/index.html
- `trace_agent()` --conceptually_related_to--> `IngestionAgent`  [INFERRED]
  weave_integration/tracer.py → README.md
- `AgentMessage` --conceptually_related_to--> `AgentMessage Shared Contract`  [EXTRACTED]
  shared/models.py → README.md
- `serve_ui()` --references--> `analyze() JS function`  [INFERRED]
  api/main.py → ui/index.html
- `run_pipeline()` --calls--> `IngestionAgent`  [EXTRACTED]
  orchestrator/pipeline.py → README.md

## Hyperedges (group relationships)
- **Multi-Agent Clinical Pipeline Flow** — readme_agent_ingestion, readme_agent_medication, readme_agent_timeline, readme_agent_risk, readme_agent_synthesis [EXTRACTED 1.00]
- **W&B Weave Tracing Integration** — weave_integration_tracer_init_weave, weave_integration_tracer_trace_agent, readme_wandb_weave [EXTRACTED 1.00]
- **API-Pipeline-Contract Data Flow** — api_main_analyze_endpoint, orchestrator_pipeline_run_pipeline, shared_models_agentmessage [INFERRED 0.95]

## Communities (16 total, 3 thin omitted)

### Community 0 - "Weave Tracing Integration"
Cohesion: 0.19
Nodes (14): IngestionAgent, MedicationAgent, RiskAgent, SynthesisAgent, TimelineAgent, Anthropic Claude API (claude-sonnet-4-20250514), ClinicalCopilot System, OpenFDA Drug Label API (+6 more)

### Community 1 - "Multi-Agent Pipeline"
Cohesion: 0.08
Nodes (24): ClinicalCopilot — Person 1 Task Sheet, code:bash (git clone https://github.com/SIDEYS/clinical-copilot), code:bash (git add agents/), code:block2 (agents/ingestion.py    ✅ complete), code:python (from shared.llm import chat  # this is all you need), code:block4 (agents/ingestion.py     — no LLM, pure Python (already done ), code:python (from shared.models import AgentMessage), code:bash (python -c ") (+16 more)

### Community 2 - "FastAPI Endpoints"
Cohesion: 0.17
Nodes (13): analyze(), analyze endpoint (POST /analyze), AnalyzeRequest, AnalyzeResponse, serve_ui(), BaseModel, _async_pipeline(), Temporary stub for testing the API.     Person 3 replaces this entire file with (+5 more)

### Community 3 - "Orchestration Pipeline"
Cohesion: 0.09
Nodes (22): ClinicalCopilot — Person 3 Task Sheet, code:bash (git clone https://github.com/SIDEYS/clinical-copilot), code:block2 (agents/synthesis.py         ✅ complete), code:block3 (tests/sample_chart.txt      ← Task 0  PUSH THIS FIRST — Pers), code:block4 (PATIENT: Jane Doe  |  DOB: 1958-03-14  |  MRN: 00291847), code:bash (git add tests/sample_chart.txt), code:bash (python -c "), code:bash (# Terminal 1) (+14 more)

### Community 4 - "UI-API Bridge"
Cohesion: 0.09
Nodes (22): API, Architecture, ClinicalCopilot 🏥, code:block1 ([Raw Clinical Text]), code:bash (# Default), code:block3 (clinical-copilot/), code:python (# shared/models.py), code:json ({) (+14 more)

### Community 5 - "Shared Data Models"
Cohesion: 0.13
Nodes (12): run(), check_interactions(), extract_medications(), run(), run(), run(), run(), AgentMessage Shared Contract (+4 more)

### Community 13 - "Community 13"
Cohesion: 0.5
Nodes (4): code:block9 (TEAM NAME: ClinicalCopilot), Screen recording script (2 min, practice once):, Submission description (pre-written, paste into AGI House):, Task 4 — Demo Prep (start at 3:30pm)

### Community 14 - "Community 14"
Cohesion: 0.5
Nodes (4): code:bash (git clone https://github.com/SIDEYS/clinical-copilot), code:block7 (ANTHROPIC_API_KEY=your_anthropic_key_here), .env.example, Environment Setup

## Knowledge Gaps
- **54 isolated node(s):** `Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med`, `Central LLM config. All agents import `chat` from here. Swap models by setting L`, `Most of the pipeline is already built. Your job: sample data, validation, demo, submission.`, `code:bash (git clone https://github.com/SIDEYS/clinical-copilot)`, `code:block2 (agents/synthesis.py         ✅ complete)` (+49 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentMessage` connect `Shared Data Models` to `FastAPI Endpoints`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `FastAPI Endpoints` to `Weave Tracing Integration`, `Shared Data Models`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Why does `IngestionAgent` connect `Weave Tracing Integration` to `FastAPI Endpoints`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `AgentMessage` (e.g. with `run()` and `run()`) actually correct?**
  _`AgentMessage` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `run_pipeline()` (e.g. with `analyze()` and `AgentMessage`) actually correct?**
  _`run_pipeline()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med`, `Central LLM config. All agents import `chat` from here. Swap models by setting L`, `Most of the pipeline is already built. Your job: sample data, validation, demo, submission.` to the rest of the system?**
  _54 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Multi-Agent Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._