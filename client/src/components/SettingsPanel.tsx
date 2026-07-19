import { useEffect, useRef, useState } from "react";
import { Settings, X, ShieldCheck, AlertTriangle, ExternalLink } from "lucide-react";
import type { LLMConfig, LLMProvider } from "../types";

export const REPO_URL = "https://github.com/vpk-11/clinical-copilot";

const PROVIDERS: { value: LLMProvider; label: string; placeholder: string; localOnly?: boolean }[] = [
  { value: "anthropic", label: "Anthropic", placeholder: "claude-sonnet-4-20250514" },
  { value: "openai", label: "OpenAI", placeholder: "gpt-4o" },
  { value: "groq", label: "Groq", placeholder: "llama-3.3-70b-versatile" },
  { value: "ollama", label: "Ollama (local only)", placeholder: "llama3", localOnly: true },
];

function isLocalHost(): boolean {
  if (typeof window === "undefined") return false;
  return ["localhost", "127.0.0.1"].includes(window.location.hostname);
}

interface SettingsPanelProps {
  config: LLMConfig;
  onChange: (config: LLMConfig) => void;
}

export default function SettingsPanel({ config, onChange }: SettingsPanelProps) {
  const [open, setOpen] = useState(false);
  const selected = PROVIDERS.find((p) => p.value === config.provider);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const firstFieldRef = useRef<HTMLSelectElement>(null);
  const localOnlyAllowed = isLocalHost();

  useEffect(() => {
    if (!open) return;
    firstFieldRef.current?.focus();

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        onClick={() => setOpen((v) => !v)}
        aria-label="LLM settings"
        aria-haspopup="dialog"
        aria-expanded={open}
        className="p-2 rounded-lg text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition-colors"
        title="LLM settings"
      >
        <Settings className="w-4 h-4" aria-hidden="true" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-20" onClick={() => setOpen(false)} />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="llm-settings-heading"
            className="absolute right-0 top-full mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-lg z-30 overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between">
              <h3 id="llm-settings-heading" className="text-sm font-semibold text-slate-700">
                LLM Settings
              </h3>
              <button
                onClick={() => {
                  setOpen(false);
                  triggerRef.current?.focus();
                }}
                aria-label="Close LLM settings"
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>

            <div className="p-4 space-y-3">
              <div className="flex gap-2 items-start bg-clinical-50 border border-clinical-100 rounded-lg p-2.5">
                <ShieldCheck className="w-4 h-4 text-clinical-600 shrink-0 mt-0.5" aria-hidden="true" />
                <p className="text-xs text-slate-600 leading-relaxed">
                  Keys stay in this tab only - sent straight to the model
                  provider as a request header, never stored server-side or
                  logged, cleared the moment you close the tab.
                </p>
              </div>

              <div>
                <label htmlFor="llm-provider" className="text-xs font-medium text-slate-600 block mb-1">
                  Provider
                </label>
                <select
                  id="llm-provider"
                  ref={firstFieldRef}
                  value={config.provider}
                  onChange={(e) =>
                    // Clear model + apiKey on provider switch — a key typed
                    // for one provider is meaningless (and wrong) for another.
                    onChange({ ...config, provider: e.target.value as LLMProvider | "", model: "", apiKey: "" })
                  }
                  className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-clinical-500"
                >
                  <option value="">Server default</option>
                  {PROVIDERS.map((p) => (
                    <option key={p.value} value={p.value} disabled={p.localOnly && !localOnlyAllowed}>
                      {p.localOnly && !localOnlyAllowed ? `${p.label} — unavailable here` : p.label}
                    </option>
                  ))}
                </select>
              </div>

              {!config.provider && (
                <div className="flex gap-2 items-start bg-red-50 border border-red-100 rounded-lg p-2.5">
                  <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Server default runs a lightweight model, rate limited for
                    demo use - fine for a quick look, not peak accuracy. Pick
                    a provider above and add your own key for better results.
                  </p>
                </div>
              )}

              {config.provider === "ollama" && !localOnlyAllowed && (
                <div className="flex gap-2 items-start bg-red-50 border border-red-100 rounded-lg p-2.5">
                  <AlertTriangle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" aria-hidden="true" />
                  <p className="text-xs text-slate-600 leading-relaxed">
                    Ollama needs a server running on the same machine as the
                    backend. It won't work on this hosted deployment - only
                    when you run ClinicalCopilot locally with Ollama installed.
                  </p>
                </div>
              )}

              {config.provider && (
                <>
                  <div>
                    <label htmlFor="llm-model" className="text-xs font-medium text-slate-600 block mb-1">
                      Model
                    </label>
                    <input
                      id="llm-model"
                      type="text"
                      value={config.model}
                      onChange={(e) => onChange({ ...config, model: e.target.value })}
                      placeholder={selected?.placeholder}
                      aria-describedby="llm-model-hint"
                      className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-clinical-500"
                    />
                    <p id="llm-model-hint" className="text-xs text-slate-400 mt-1">
                      Leave blank to use {selected?.placeholder}
                    </p>
                  </div>

                  {config.provider !== "ollama" && (
                    <div>
                      <label htmlFor="llm-api-key" className="text-xs font-medium text-slate-600 block mb-1">
                        API Key <span className="text-red-500">*</span> required
                      </label>
                      <input
                        id="llm-api-key"
                        type="password"
                        value={config.apiKey}
                        onChange={(e) => onChange({ ...config, apiKey: e.target.value })}
                        placeholder={`Paste your ${selected?.label} key`}
                        aria-describedby="llm-api-key-hint"
                        autoComplete="off"
                        className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-clinical-500"
                      />
                      <p id="llm-api-key-hint" className="text-xs text-slate-400 mt-1">
                        No server-side key for this provider - without one, requests will fail.
                      </p>
                    </div>
                  )}
                </>
              )}

              <a
                href={REPO_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-clinical-600 transition-colors pt-1"
              >
                <ExternalLink className="w-3.5 h-3.5" aria-hidden="true" />
                View source on GitHub
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
