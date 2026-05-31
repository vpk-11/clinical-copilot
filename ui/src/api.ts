import type { AnalysisResult } from "./types";

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
  const res = await fetch("/upload", { method: "POST", body: form });
  return handleResponse(res);
}

export async function normalizeText(
  text: string,
  patientId: string
): Promise<{ normalized_text: string; original_char_count: number; normalized_char_count: number }> {
  const res = await fetch("/normalize", {
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
  const res = await fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, patient_id: patientId }),
  });
  return handleResponse(res);
}
