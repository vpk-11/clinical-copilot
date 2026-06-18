import type { AnalysisResult } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

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
  patientId: string
): Promise<{ normalized_text: string; original_char_count: number; normalized_char_count: number; status: string; status_reason: string }> {
  const res = await fetch(`${API_BASE}/normalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, patient_id: patientId }),
  });
  return handleResponse(res);
}

export async function analyzeChart(
  text: string,
  patientId: string
): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, patient_id: patientId }),
  });
  return handleResponse(res);
}
