import { useState, useCallback } from "react";
import { Activity, ChevronDown, ChevronUp, Edit3, Loader2, RotateCcw } from "lucide-react";
import FileUpload from "./components/FileUpload";
import ResultsDashboard from "./components/ResultsDashboard";
import { analyzeChart } from "./api";
import type { AnalysisResult, AppStep } from "./types";

export default function App() {
  const [step, setStep] = useState<AppStep>("upload");
  const [patientId, setPatientId] = useState("DEMO-001");
  const [normalizedText, setNormalizedText] = useState("");
  const [filenames, setFilenames] = useState<string[]>([]);
  const [showPreview, setShowPreview] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);

  const handleFileReady = useCallback((text: string, names: string[]) => {
    setNormalizedText(text);
    setFilenames(names);
    setStep("preview");
    setError("");
    setShowPreview(false);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!normalizedText.trim()) return;
    setStep("analyzing");
    setError("");
    try {
      const data = await analyzeChart(normalizedText, patientId);
      setResult(data);
      setStep("results");
    } catch (e) {
      setError((e as Error).message);
      setStep("preview");
    }
  }, [normalizedText, patientId]);

  const handleReset = useCallback(() => {
    setStep("upload");
    setNormalizedText("");
    setFilenames([]);
    setResult(null);
    setError("");
    setShowPreview(false);
    setIsEditing(false);
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-clinical-500 rounded-lg">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 leading-none">
                ClinicalCopilot
              </h1>
              <p className="text-xs text-slate-500 mt-0.5">
                Multi-agent chart analysis
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {step !== "upload" && (
              <button
                onClick={handleReset}
                className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 transition-colors"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Start over
              </button>
            )}
            <span className="text-xs text-slate-400">
              5 parallel agents · W&B Weave
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 py-8 space-y-6">
        {/* Upload step */}
        {(step === "upload" || step === "preview") && (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-4">
              Upload Clinical Document
            </h2>
            <FileUpload
              patientId={patientId}
              onPatientIdChange={setPatientId}
              onReady={handleFileReady}
            />
          </div>
        )}

        {/* Normalized text preview + analyze */}
        {step === "preview" && normalizedText && (
          <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-700">
                  Structured Clinical Text
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Normalized from {filenames.join(", ")} by InputAgent — review before analysis
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditing((v) => !v)}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors"
                >
                  <Edit3 className="w-3 h-3" />
                  {isEditing ? "Done editing" : "Edit"}
                </button>
                <button
                  onClick={() => setShowPreview((v) => !v)}
                  className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors"
                >
                  {showPreview ? (
                    <>
                      <ChevronUp className="w-3 h-3" /> Hide
                    </>
                  ) : (
                    <>
                      <ChevronDown className="w-3 h-3" /> Preview
                    </>
                  )}
                </button>
              </div>
            </div>

            {showPreview && (
              <div className="p-4 border-b border-slate-200 bg-slate-50">
                {isEditing ? (
                  <textarea
                    value={normalizedText}
                    onChange={(e) => setNormalizedText(e.target.value)}
                    rows={16}
                    className="w-full text-xs font-mono text-slate-700 bg-white border border-slate-300 rounded-lg p-3 focus:outline-none focus:ring-2 focus:ring-clinical-500 resize-y"
                  />
                ) : (
                  <pre className="text-xs font-mono text-slate-700 whitespace-pre-wrap max-h-72 overflow-y-auto">
                    {normalizedText}
                  </pre>
                )}
              </div>
            )}

            <div className="px-5 py-4 flex items-center gap-4">
              {error && (
                <p className="text-xs text-red-600 flex-1">{error}</p>
              )}
              <div className="flex-1" />
              <button
                onClick={handleAnalyze}
                className="inline-flex items-center gap-2 bg-clinical-500 hover:bg-clinical-600 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-colors shadow-sm"
              >
                <Activity className="w-4 h-4" />
                Run Full Analysis
              </button>
            </div>
          </div>
        )}

        {/* Analyzing state */}
        {step === "analyzing" && (
          <div className="bg-white border border-slate-200 rounded-xl p-12 shadow-sm flex flex-col items-center gap-5">
            <Loader2 className="w-12 h-12 text-clinical-500 animate-spin" />
            <div className="text-center">
              <p className="text-base font-semibold text-slate-700">
                Running 5 parallel agents
              </p>
              <p className="text-sm text-slate-500 mt-1">
                Ingestion · Medication · Timeline · Risk · Synthesis
              </p>
            </div>
            <div className="flex flex-col gap-1.5 w-64">
              {[
                "Extracting clinical sections...",
                "Identifying medications + OpenFDA lookup...",
                "Building medical timeline...",
                "Detecting risk flags...",
                "Generating reports...",
              ].map((label, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div
                    className="w-1.5 h-1.5 rounded-full bg-clinical-400 animate-pulse"
                    style={{ animationDelay: `${i * 200}ms` }}
                  />
                  <span className="text-xs text-slate-500">{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Results */}
        {step === "results" && result && (
          <ResultsDashboard result={result} />
        )}
      </main>
    </div>
  );
}
