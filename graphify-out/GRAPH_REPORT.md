# Graph Report - .  (2026-05-31)

## Corpus Check
- Corpus is ~2,195 words - fits in a single context window. You may not need a graph.

## Summary
- 41 nodes · 45 edges · 13 communities (11 shown, 2 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 6 edges (avg confidence: 0.89)
- Token cost: 4,200 input · 1,800 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Weave Tracing Integration|Weave Tracing Integration]]
- [[_COMMUNITY_Multi-Agent Pipeline|Multi-Agent Pipeline]]
- [[_COMMUNITY_FastAPI Endpoints|FastAPI Endpoints]]
- [[_COMMUNITY_Orchestration Pipeline|Orchestration Pipeline]]
- [[_COMMUNITY_UI-API Bridge|UI-API Bridge]]
- [[_COMMUNITY_Shared Data Models|Shared Data Models]]
- [[_COMMUNITY_Health Check|Health Check]]
- [[_COMMUNITY_FastAPI App|FastAPI App]]

## God Nodes (most connected - your core abstractions)
1. `run_pipeline()` - 8 edges
2. `trace_agent()` - 5 edges
3. `AgentMessage` - 5 edges
4. `AnalyzeResponse` - 5 edges
5. `IngestionAgent` - 5 edges
6. `init_weave()` - 4 edges
7. `MedicationAgent` - 4 edges
8. `Anthropic Claude API (claude-sonnet-4-20250514)` - 4 edges
9. `analyze()` - 3 edges
10. `analyze endpoint (POST /analyze)` - 3 edges

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

## Communities (13 total, 2 thin omitted)

### Community 0 - "Weave Tracing Integration"
Cohesion: 0.29
Nodes (7): ClinicalCopilot System, W&B Weave Audit Trail, init_weave(), Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med, trace_agent(), W&B wandb.init call, weave.op decorator wrapping

### Community 1 - "Multi-Agent Pipeline"
Cohesion: 0.48
Nodes (7): IngestionAgent, MedicationAgent, RiskAgent, SynthesisAgent, TimelineAgent, Anthropic Claude API (claude-sonnet-4-20250514), OpenFDA Drug Label API

### Community 2 - "FastAPI Endpoints"
Cohesion: 0.47
Nodes (4): analyze(), AnalyzeRequest, AnalyzeResponse, BaseModel

### Community 3 - "Orchestration Pipeline"
Cohesion: 0.4
Nodes (4): Temporary stub for testing the API.     Person 3 replaces this entire file with, run_pipeline(), Pipeline Stub Design, Parallel asyncio Agent Fan-out Pattern

### Community 4 - "UI-API Bridge"
Cohesion: 0.5
Nodes (4): analyze endpoint (POST /analyze), serve_ui(), analyze() JS function, renderResults() JS function

### Community 5 - "Shared Data Models"
Cohesion: 0.5
Nodes (3): AgentMessage Shared Contract, AgentMessage, TypedDict

## Knowledge Gaps
- **10 isolated node(s):** `Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med`, `Temporary stub for testing the API.     Person 3 replaces this entire file with`, `W&B wandb.init call`, `weave.op decorator wrapping`, `health endpoint (GET /health)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run_pipeline()` connect `Orchestration Pipeline` to `Multi-Agent Pipeline`, `FastAPI Endpoints`, `UI-API Bridge`, `Shared Data Models`?**
  _High betweenness centrality (0.406) - this node is a cross-community bridge._
- **Why does `IngestionAgent` connect `Multi-Agent Pipeline` to `Weave Tracing Integration`, `Orchestration Pipeline`?**
  _High betweenness centrality (0.319) - this node is a cross-community bridge._
- **Why does `AgentMessage` connect `Shared Data Models` to `FastAPI Endpoints`, `Orchestration Pipeline`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `run_pipeline()` (e.g. with `analyze()` and `AgentMessage`) actually correct?**
  _`run_pipeline()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AgentMessage` (e.g. with `AnalyzeResponse` and `run_pipeline()`) actually correct?**
  _`AgentMessage` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AnalyzeResponse` (e.g. with `AgentMessage` and `renderResults() JS function`) actually correct?**
  _`AnalyzeResponse` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med`, `Temporary stub for testing the API.     Person 3 replaces this entire file with`, `W&B wandb.init call` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._