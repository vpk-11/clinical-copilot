import type { AnalysisResult, LLMConfig } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

const PROVIDER_KEY_HEADERS: Record<string, string> = {
  anthropic: "x-anthropic-api-key",
  openai: "x-openai-api-key",
  groq: "x-groq-api-key",
};

// BYOK headers only - never sent in the request body, never persisted
// server-side. See api/main.py::_build_llm_config_from_headers.
function llmHeaders(config?: LLMConfig): Record<string, string> {
  if (!config || !config.provider) return {};
  const headers: Record<string, string> = { "x-llm-provider": config.provider };
  if (config.model) headers["x-llm-model"] = config.model;
  const keyHeader = PROVIDER_KEY_HEADERS[config.provider];
  if (keyHeader && config.apiKey) headers[keyHeader] = config.apiKey;
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function uploadFile(
  file: File
): Promise<{ text: string; filename: string; char_count: number }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form });
  return handleResponse(res);
}

export async function normalizeText(
  text: string,
  patientId: string,
  llmConfig?: LLMConfig
): Promise<{ normalized_text: string; original_char_count: number; normalized_char_count: number; status: string; status_reason: string }> {
  const res = await fetch(`${API_BASE}/normalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...llmHeaders(llmConfig) },
    body: JSON.stringify({ text, patient_id: patientId }),
  });
  return handleResponse(res);
}

export async function analyzeChart(
  text: string,
  patientId: string,
  llmConfig?: LLMConfig
): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...llmHeaders(llmConfig) },
    body: JSON.stringify({ text, patient_id: patientId }),
  });
  return handleResponse(res);
}

export interface SampleGroup {
  group: string;
  demo_id: string;
  patient: string;
  label: string;
  files: string[];
}

export interface SamplesResponse {
  groups: SampleGroup[];
}

export async function listSamples(): Promise<SamplesResponse> {
  const res = await fetch(`${API_BASE}/samples`);
  return handleResponse(res);
}

export function sampleDownloadUrl(filename: string): string {
  return `${API_BASE}/samples/${encodeURIComponent(filename)}`;
}

export function sampleZipUrl(group: string): string {
  return `${API_BASE}/samples/zip/${encodeURIComponent(group)}`;
}
