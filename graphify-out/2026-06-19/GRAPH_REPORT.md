# Graph Report - clinical-copilot  (2026-06-19)

## Corpus Check
- 36 files · ~13,572 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 163 nodes · 209 edges · 25 communities (22 shown, 3 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e5931bed`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Task Documentation|Task Documentation]]
- [[_COMMUNITY_Agent Implementations|Agent Implementations]]
- [[_COMMUNITY_FastAPI + Contract Layer|FastAPI + Contract Layer]]
- [[_COMMUNITY_Multi-Agent Pipeline Docs|Multi-Agent Pipeline Docs]]
- [[_COMMUNITY_Clinical Test Cases|Clinical Test Cases]]
- [[_COMMUNITY_LiteLLM Config|LiteLLM Config]]
- [[_COMMUNITY_Environment Setup|Environment Setup]]
- [[_COMMUNITY_Task Scaffolding|Task Scaffolding]]
- [[_COMMUNITY_Weave Tracing|Weave Tracing]]
- [[_COMMUNITY_Orchestrator Pipeline|Orchestrator Pipeline]]
- [[_COMMUNITY_Shared Models|Shared Models]]
- [[_COMMUNITY_Risk Deterministic Flags|Risk Deterministic Flags]]
- [[_COMMUNITY_Test Runner|Test Runner]]
- [[_COMMUNITY_Agents Module|Agents Module]]
- [[_COMMUNITY_Shared Module|Shared Module]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]

## God Nodes (most connected - your core abstractions)
1. `run()` - 17 edges
2. `chat()` - 10 edges
3. `ClinicalCopilot` - 9 edges
4. `extract_medications()` - 8 edges
5. `AgentMessage` - 8 edges
6. `run()` - 6 edges
7. `analyze()` - 6 edges
8. `run()` - 6 edges
9. `run_pipeline()` - 6 edges
10. `_med_key()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Critical lab: Glucose 512 mg/dL, bicarb 8, anion gap 28` --conceptually_related_to--> `Clinical threshold constants (K>6.0 HIGH, BNP>1000 HIGH, SpO2<94, etc.)`  [INFERRED]
  tests/case_04_dka.txt → agents/risk.py
- `Critical lab: K 6.1 (CRITICALLY HIGH)` --conceptually_related_to--> `Clinical threshold constants (K>6.0 HIGH, BNP>1000 HIGH, SpO2<94, etc.)`  [INFERRED]
  tests/sample_chart.txt → agents/risk.py
- `AnalyzeResponse` --shares_data_with--> `AgentMessage`  [INFERRED]
  api/main.py → agents/medication.py
- `analyze()` --calls--> `run_pipeline()`  [INFERRED]
  api/main.py → orchestrator/pipeline.py
- `analyze()` --calls--> `generate_doctor_report()`  [INFERRED]
  api/main.py → shared/reports.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **All LLM-calling agents share the chat() interface via shared/llm.py** — agents_timeline_run, agents_medication_extract_medications, agents_risk_run, agents_synthesis_run, shared_llm_chat [EXTRACTED 1.00]
- **Pipeline execution order: ingestion -> [medication || timeline] -> risk -> synthesis** — agents_ingestion_run, agents_medication_run, agents_timeline_run, agents_risk_run, agents_synthesis_run [EXTRACTED 1.00]
- **Five test cases covering five different acute emergencies for full pipeline validation** — tests_sample_chart_jane_doe, tests_case_02_sepsis_john_smith, tests_case_03_stemi_robert_chen, tests_case_04_dka_maria_gonzalez, tests_case_05_stroke_dorothy_williams [EXTRACTED 1.00]

## Communities (25 total, 3 thin omitted)

### Community 0 - "Task Documentation"
Cohesion: 0.14
Nodes (13): `/analyze` response, API, Architecture, Authentication, Backend, ClinicalCopilot, Frontend, LLM Provider (+5 more)

### Community 1 - "Agent Implementations"
Cohesion: 0.61
Nodes (7): check_interactions(), extract_medications(), _fallback_extract_medications(), _med_key(), _merge_medications(), run(), str

### Community 2 - "FastAPI + Contract Layer"
Cohesion: 0.20
Nodes (9): AgentMessage, run(), _async_pipeline(), Parallel asyncio fan-out: medication and timeline run concurrently, Temporary stub for testing the API.     Person 3 replaces this entire file with, run_pipeline(), Pipeline Stub Design, AgentMessage (+1 more)

### Community 4 - "Multi-Agent Pipeline Docs"
Cohesion: 0.33
Nodes (5): init_weave(), Decorator factory. Wraps an agent run() function with a Weave op.     Usage: med, trace_agent(), W&B wandb.init call, weave.op decorator wrapping

### Community 5 - "Clinical Test Cases"
Cohesion: 0.16
Nodes (14): _add_flag(), Clinical threshold constants (K>6.0 HIGH, BNP>1000 HIGH, SpO2<94, etc.), _deterministic_flags(), _max_number_after(), _merge_flags(), _numbers_after(), Diagnosis: DKA severe — pH 7.08, bicarb 8, glucose 512, Critical lab: Glucose 512 mg/dL, bicarb 8, anion gap 28 (+6 more)

### Community 6 - "LiteLLM Config"
Cohesion: 0.14
Nodes (11): FlagBadgeProps, SEVERITY_DOT, SEVERITY_STYLES, ResultsDashboardProps, AnalysisResult, AppStep, Interaction, Medication (+3 more)

### Community 7 - "Environment Setup"
Cohesion: 0.18
Nodes (13): analyze(), AnalyzeRequest, AnalyzeResponse, api_key_middleware(), normalize(), NormalizeRequest, NormalizeResponse, Run InputAgent to normalize raw text into structured clinical chart format. (+5 more)

### Community 8 - "Task Scaffolding"
Cohesion: 0.25
Nodes (10): Extract text from an uploaded PDF, DOCX, MD, or TXT file., upload_file(), _extract_docx(), _extract_pdf(), _extract_pdf_fallback(), extract_text(), File text extraction. Pure Python, no LLM. Uses pdfplumber for PDFs — extracts t, Uses pdfplumber for spatial-aware extraction — captures text that sits     besid (+2 more)

### Community 10 - "Weave Tracing"
Cohesion: 0.50
Nodes (4): Diagnosis: Septic shock — urosepsis source, Critical vital: BP 82/54 (septic hypotension), Patient: John Smith — septic shock from urosepsis, Critical lab: Lactate 4.2 mmol/L (septic shock marker)

### Community 11 - "Orchestrator Pipeline"
Cohesion: 0.50
Nodes (4): Diagnosis: Acute ischemic stroke — right MCA occlusion, NIHSS 14, Patient: Dorothy Williams — acute ischemic stroke (right MCA), Critical finding: INR 1.4 subtherapeutic (on warfarin for AFib), Treatment: IV tPA (alteplase) 0.9mg/kg + mechanical thrombectomy

### Community 12 - "Shared Models"
Cohesion: 0.67
Nodes (3): check(), End-to-end test runner for all patient cases. Usage: python tests/run_all.py, run_case()

### Community 13 - "Risk Deterministic Flags"
Cohesion: 0.67
Nodes (3): Diagnosis: Anterior wall STEMI — cath lab activation, Patient: Robert Chen — anterior STEMI, Critical lab: Troponin I 4.8 rising to 9.2 ng/mL

### Community 16 - "Agents Module"
Cohesion: 0.14
Nodes (13): InputAgent: normalizes raw, messy clinical text into structured chart format. Th, run(), run(), run(), SOAP Note output structure (Subjective/Objective/Assessment/Plan), _fallback_events(), _merge_events(), run() (+5 more)

### Community 25 - "Community 25"
Cohesion: 0.27
Nodes (7): ACCEPTED_TYPES, FileEntry, FileUploadProps, analyzeChart(), handleResponse(), normalizeText(), uploadFile()

## Knowledge Gaps
- **43 isolated node(s):** `Request`, `UploadFile`, `What It Does`, `Architecture`, `Stack` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `run()` connect `Agents Module` to `Agent Implementations`, `FastAPI + Contract Layer`, `Shared Models`, `Clinical Test Cases`?**
  _High betweenness centrality (0.149) - this node is a cross-community bridge._
- **Why does `AgentMessage` connect `FastAPI + Contract Layer` to `Agents Module`, `Agent Implementations`, `Environment Setup`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `AnalyzeResponse` connect `Environment Setup` to `FastAPI + Contract Layer`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `chat()` (e.g. with `run()` and `run()`) actually correct?**
  _`chat()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `AgentMessage` (e.g. with `AnalyzeResponse` and `run_pipeline()`) actually correct?**
  _`AgentMessage` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Request`, `UploadFile`, `Extract text from an uploaded PDF, DOCX, MD, or TXT file.` to the rest of the system?**
  _57 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Task Documentation` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._