export interface RiskFlag {
  flag: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  evidence?: string;
}

export interface Medication {
  name: string;
  dose: string;
  frequency: string;
}

export interface Interaction {
  drug: string;
  warnings: string;
}

export interface TimelineEvent {
  date: string;
  event: string;
  category: string;
}

export interface SoapNote {
  subjective: string | string[];
  objective: string | string[];
  assessment: string | string[];
  plan: string | string[];
}

export interface AnalysisResult {
  trace_id: string;
  pipeline_status: string;
  pipeline_status_reason: string;
  doctor_report: string;
  patient_report: string;
  soap_note: SoapNote;
  red_flags: string[];
  summary: string;
  medications: Medication[];
  interactions: Interaction[];
  timeline_events: TimelineEvent[];
  risk_flags: RiskFlag[];
  weave_url: string;
  model_used: string;
  used_byok: boolean;
}

export type AppStep = "upload" | "preview" | "analyzing" | "results";

export type LLMProvider = "anthropic" | "openai" | "groq" | "ollama";

export interface LLMConfig {
  provider: LLMProvider | "";
  model: string;
  apiKey: string;
}

export const DEFAULT_LLM_CONFIG: LLMConfig = { provider: "", model: "", apiKey: "" };
