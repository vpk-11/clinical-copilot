# Graph Report - clinical-copilot  (2026-05-31)

## Corpus Check
- 19 files · ~5,995 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 143 nodes · 181 edges · 22 communities (19 shown, 3 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.64)
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
- [[_COMMUNITY_Community 16|Community 16]]

## God Nodes (most connected - your core abstractions)
1. `AgentMessage` - 17 edges
2. `ClinicalCopilot 🏥` - 14 edges
3. `ClinicalCopilot — Person 3 Task Sheet` - 13 edges
4. `ClinicalCopilot — Person 1 Task Sheet` - 13 edges
5. `chat()` - 11 edges
6. `run_pipeline()` - 11 edges
7. `trace_agent()` - 6 edges
8. `run()` - 6 edges
9. `extract_medications()` - 6 edges
10. `str` - 6 edges

## Surprising Connections (you probably didn't know these)
- `AnalyzeResponse` --shares_data_with--> `renderResults() JS function`  [INFERRED]
  /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/api/main.py → ui/index.html
- `trace_agent()` --conceptually_related_to--> `IngestionAgent`  [INFERRED]
  /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/weave_integration/tracer.py → README.md
- `AgentMessage` --uses--> `AgentMessage`  [INFERRED]
  agents/timeline.py → /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/shared/models.py
- `AgentMessage` --uses--> `AgentMessage`  [INFERRED]
  agents/medication.py → /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/shared/models.py
- `AgentMessage` --uses--> `AgentMessage`  [INFERRED]
  agents/risk.py → /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/shared/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Multi-Agent Clinical Pipeline Flow** — readme_agent_ingestion, readme_agent_medication, readme_agent_timeline, readme_agent_risk, readme_agent_synthesis [EXTRACTED 1.00]
- **W&B Weave Tracing Integration** — weave_integration_tracer_init_weave, weave_integration_tracer_trace_agent, readme_wandb_weave [EXTRACTED 1.00]
- **API-Pipeline-Contract Data Flow** — api_main_analyze_endpoint, orchestrator_pipeline_run_pipeline, shared_models_agentmessage [INFERRED 0.95]

## Communities (22 total, 3 thin omitted)

### Community 0 - "Weave Tracing Integration"
Cohesion: 0.18
Nodes (14): IngestionAgent, MedicationAgent, RiskAgent, SynthesisAgent, TimelineAgent, Anthropic Claude API (claude-sonnet-4-20250514), ClinicalCopilot System, OpenFDA Drug Label API (+6 more)

### Community 1 - "Multi-Agent Pipeline"
Cohesion: 0.11
Nodes (18): API, Architecture, ClinicalCopilot 🏥, .env.example, Environment Setup, External APIs Used, Hackathon Submission, Judging Criteria Coverage (+10 more)

### Community 2 - "FastAPI Endpoints"
Cohesion: 0.18
Nodes (15): analyze(), analyze endpoint (POST /analyze), AnalyzeRequest, AnalyzeResponse, health(), serve_ui(), BaseModel, _async_pipeline() (+7 more)

### Community 3 - "Orchestration Pipeline"
Cohesion: 0.11
Nodes (17): ClinicalCopilot — Person 3 Task Sheet, Do this IMMEDIATELY. Person 1 needs it to test agents., ⚡ FIRST: Clone and set up, If You Get Stuck, Most of the pipeline is already built. Your job: sample data, validation, demo, submission., Role: Pipeline Lead + Demo Owner, Screen recording script (2 min, practice once):, Submission Checklist (+9 more)

### Community 4 - "UI-API Bridge"
Cohesion: 0.18
Nodes (12): AgentMessage, str, run(), _fallback_events(), _merge_events(), AgentMessage, str, run() (+4 more)

### Community 5 - "Shared Data Models"
Cohesion: 0.25
Nodes (6): AgentMessage, str, run(), AgentMessage Shared Contract, AgentMessage, TypedDict

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (14): ClinicalCopilot — Person 1 Task Sheet, ⚡ FIRST: Clone and set up, If You Get Stuck, Push Your Prompt Tweaks, Role: ML Agent Engineer, Sync Checkpoints, Task 1 — Verify IngestionAgent, Task 2 — Verify + Tune MedicationAgent (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.42
Nodes (9): _add_flag(), _deterministic_flags(), _max_number_after(), _merge_flags(), _numbers_after(), AgentMessage, str, run() (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.47
Nodes (8): check_interactions(), extract_medications(), _fallback_extract_medications(), _med_key(), _merge_medications(), AgentMessage, str, run()

## Knowledge Gaps
- **46 isolated node(s):** `str`, `int`, `Most of the pipeline is already built. Your job: sample data, validation, demo, submission.`, `⚡ FIRST: Clone and set up`, `What's Already Done For You` (+41 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentMessage` connect `Shared Data Models` to `FastAPI Endpoints`, `UI-API Bridge`, `Community 14`, `Community 15`?**
  _High betweenness centrality (0.187) - this node is a cross-community bridge._
- **Why does `run_pipeline()` connect `FastAPI Endpoints` to `Weave Tracing Integration`, `Shared Data Models`?**
  _High betweenness centrality (0.142) - this node is a cross-community bridge._
- **Why does `IngestionAgent` connect `Weave Tracing Integration` to `FastAPI Endpoints`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `AgentMessage` (e.g. with `AgentMessage` and `str`) actually correct?**
  _`AgentMessage` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med`, `str`, `int` to the rest of the system?**
  _52 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Multi-Agent Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Orchestration Pipeline` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._