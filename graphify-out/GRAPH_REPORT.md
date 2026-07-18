# Graph Report - clinical-copilot  (2026-07-18)

## Corpus Check
- 39 files · ~15,908 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 289 nodes · 396 edges · 33 communities (29 shown, 4 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 11 edges (avg confidence: 0.72)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `feb54179`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Task Documentation|Task Documentation]]
- [[_COMMUNITY_Agent Implementations|Agent Implementations]]
- [[_COMMUNITY_FastAPI + Contract Layer|FastAPI + Contract Layer]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Clinical Test Cases|Clinical Test Cases]]
- [[_COMMUNITY_LiteLLM Config|LiteLLM Config]]
- [[_COMMUNITY_Environment Setup|Environment Setup]]
- [[_COMMUNITY_Task Scaffolding|Task Scaffolding]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Weave Tracing|Weave Tracing]]
- [[_COMMUNITY_Orchestrator Pipeline|Orchestrator Pipeline]]
- [[_COMMUNITY_Shared Models|Shared Models]]
- [[_COMMUNITY_Risk Deterministic Flags|Risk Deterministic Flags]]
- [[_COMMUNITY_Test Runner|Test Runner]]
- [[_COMMUNITY_Agents Module|Agents Module]]
- [[_COMMUNITY_Shared Module|Shared Module]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]

## God Nodes (most connected - your core abstractions)
1. `run()` - 16 edges
2. `compilerOptions` - 16 edges
3. `AgentMessage` - 14 edges
4. `PROJECT_CONTEXT` - 14 edges
5. `chat()` - 13 edges
6. `ClinicalCopilot` - 12 edges
7. `run()` - 9 edges
8. `ClinicalCopilot — Session Plan` - 9 edges
9. `analyze()` - 8 edges
10. `Core Stack` - 8 edges

## Surprising Connections (you probably didn't know these)
- `analyze()` --calls--> `run_pipeline()`  [INFERRED]
  api/main.py → orchestrator/pipeline.py
- `analyze()` --calls--> `generate_doctor_report()`  [INFERRED]
  api/main.py → /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/shared/reports.py
- `generate_patient_report()` --calls--> `chat()`  [INFERRED]
  /Users/vpk11/Library/CloudStorage/OneDrive-Personal/Documents/Development/clinicalcopilot/shared/reports.py → shared/llm.py
- `run_case()` --calls--> `run()`  [EXTRACTED]
  tests/run_all.py → agents/risk.py
- `run_case()` --calls--> `run()`  [EXTRACTED]
  tests/run_all.py → agents/synthesis.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **All LLM-calling agents share the chat() interface via shared/llm.py** — agents_timeline_run, agents_medication_extract_medications, agents_risk_run, agents_synthesis_run, shared_llm_chat [EXTRACTED 1.00]
- **Pipeline execution order: ingestion -> [medication || timeline] -> risk -> synthesis** — agents_ingestion_run, agents_medication_run, agents_timeline_run, agents_risk_run, agents_synthesis_run [EXTRACTED 1.00]
- **Five test cases covering five different acute emergencies for full pipeline validation** — tests_sample_chart_jane_doe, tests_case_02_sepsis_john_smith, tests_case_03_stemi_robert_chen, tests_case_04_dka_maria_gonzalez, tests_case_05_stroke_dorothy_williams [EXTRACTED 1.00]

## Communities (33 total, 4 thin omitted)

### Community 0 - "Task Documentation"
Cohesion: 0.11
Nodes (17): `/analyze` response, API, Architecture, Authentication, Backend, Bring your own key, Changelog, ClinicalCopilot (+9 more)

### Community 1 - "Agent Implementations"
Cohesion: 0.07
Nodes (26): AI / LLM Layer, API / Router Surface, Architecture Summary, Backend, Cleanup Notes, Code Quality Flags, Core Stack, Current State (+18 more)

### Community 2 - "FastAPI + Contract Layer"
Cohesion: 0.08
Nodes (24): dependencies, react, react-dom, devDependencies, lucide-react, react-dropzone, react-markdown, remark-gfm (+16 more)

### Community 3 - "Community 3"
Cohesion: 0.19
Nodes (14): check_interactions(), extract_medications(), _fallback_extract_medications(), _med_key(), _merge_medications(), AgentMessage, run(), _async_pipeline() (+6 more)

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (3): Diagnosis: DKA severe — pH 7.08, bicarb 8, glucose 512, Critical lab: Glucose 512 mg/dL, bicarb 8, anion gap 28, Patient: Maria Gonzalez — severe DKA (T1DM, missed insulin)

### Community 5 - "Clinical Test Cases"
Cohesion: 0.40
Nodes (5): Critical lab: BNP 1840 pg/mL (CRITICALLY HIGH), Diagnosis: Acute decompensated CHF (EF 35%), Critical lab: K 6.1 (CRITICALLY HIGH), Patient: Jane Doe — CHF decompensation with hyperkalemia, Drug combo: Lisinopril + Spironolactone (ACE + K-sparing diuretic)

### Community 6 - "LiteLLM Config"
Cohesion: 0.09
Nodes (19): FlagBadge(), FlagBadgeProps, SEVERITY_DOT, SEVERITY_STYLES, ReportPanelProps, ResultsDashboardProps, PROVIDERS, SettingsPanelProps (+11 more)

### Community 7 - "Environment Setup"
Cohesion: 0.11
Nodes (20): Kept in its own module to avoid a circular import between main.py and the route, analyze(), AnalyzeRequest, AnalyzeResponse, api_key_middleware(), _build_llm_config_from_headers(), list_samples(), normalize() (+12 more)

### Community 8 - "Task Scaffolding"
Cohesion: 0.16
Nodes (14): ACCEPTED_TYPES, FileEntry, FileUploadProps, analyzeChart(), handleResponse(), listSamples(), llmHeaders(), normalizeText() (+6 more)

### Community 9 - "Community 9"
Cohesion: 0.11
Nodes (17): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+9 more)

### Community 10 - "Weave Tracing"
Cohesion: 0.50
Nodes (4): Diagnosis: Septic shock — urosepsis source, Critical vital: BP 82/54 (septic hypotension), Patient: John Smith — septic shock from urosepsis, Critical lab: Lactate 4.2 mmol/L (septic shock marker)

### Community 11 - "Orchestrator Pipeline"
Cohesion: 0.50
Nodes (4): Diagnosis: Acute ischemic stroke — right MCA occlusion, NIHSS 14, Patient: Dorothy Williams — acute ischemic stroke (right MCA), Critical finding: INR 1.4 subtherapeutic (on warfarin for AFib), Treatment: IV tPA (alteplase) 0.9mg/kg + mechanical thrombectomy

### Community 12 - "Shared Models"
Cohesion: 0.17
Nodes (11): Backend (Python), Before You Start — Two Gates, ClinicalCopilot — Session Plan, Dependency Upgrade Targets, Done When, Frontend (React + Vite), Project Structure Cleanup, Reliability Fixes (+3 more)

### Community 13 - "Risk Deterministic Flags"
Cohesion: 0.67
Nodes (3): Diagnosis: Anterior wall STEMI — cath lab activation, Patient: Robert Chen — anterior STEMI, Critical lab: Troponin I 4.8 rising to 9.2 ng/mL

### Community 16 - "Agents Module"
Cohesion: 0.13
Nodes (26): run(), AgentMessage, InputAgent: normalizes raw, messy clinical text into structured chart format. Th, run(), _add_flag(), _deterministic_flags(), _max_number_after(), _merge_flags() (+18 more)

### Community 29 - "Community 29"
Cohesion: 0.50
Nodes (3): Issue, Pharmacy / Neurology Note - Anticoagulation Management, Plan

### Community 32 - "Community 32"
Cohesion: 0.25
Nodes (10): Extract text from an uploaded PDF, DOCX, MD, or TXT file., upload_file(), _extract_docx(), _extract_pdf(), _extract_pdf_fallback(), extract_text(), File text extraction. Pure Python, no LLM. Uses pdfplumber for PDFs — extracts t, Uses pdfplumber for spatial-aware extraction — captures text that sits     besid (+2 more)

## Knowledge Gaps
- **117 isolated node(s):** `What It Does`, `Architecture`, `Stack`, `Backend`, `Frontend` (+112 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentMessage` connect `Agents Module` to `Community 3`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `run()` connect `Agents Module` to `Environment Setup`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `run()` connect `Agents Module` to `Community 3`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `AgentMessage` (e.g. with `AgentMessage` and `AgentMessage`) actually correct?**
  _`AgentMessage` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `chat()` (e.g. with `run()` and `run()`) actually correct?**
  _`chat()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `What It Does`, `Architecture`, `Stack` to the rest of the system?**
  _131 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Task Documentation` be split into smaller, more focused modules?**
  _Cohesion score 0.1111111111111111 - nodes in this community are weakly interconnected._