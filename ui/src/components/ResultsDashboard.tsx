import { useState } from "react";
import { ExternalLink, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";
import type { AnalysisResult } from "../types";
import FlagBadge from "./FlagBadge";
import ReportPanel from "./ReportPanel";

interface ResultsDashboardProps {
  result: AnalysisResult;
}

export default function ResultsDashboard({ result }: ResultsDashboardProps) {
  const [showMeds, setShowMeds] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);
  const [activeTab, setActiveTab] = useState<"doctor" | "patient">("doctor");

  const highFlags = result.risk_flags.filter((f) => f.severity === "HIGH");
  const otherFlags = result.risk_flags.filter((f) => f.severity !== "HIGH");

  return (
    <div className="space-y-5">
      {/* Risk flags banner */}
      {highFlags.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <h2 className="text-sm font-semibold text-red-700">
              {highFlags.length} Critical Flag{highFlags.length > 1 ? "s" : ""}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {highFlags.map((f, i) => (
              <FlagBadge key={i} flag={f} showEvidence />
            ))}
          </div>
        </div>
      )}

      {/* All flags */}
      {otherFlags.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Additional Findings
          </h2>
          <div className="flex flex-wrap gap-2">
            {otherFlags.map((f, i) => (
              <FlagBadge key={i} flag={f} />
            ))}
          </div>
        </div>
      )}

      {/* Reports — side-by-side on desktop, tabs on mobile */}
      <div>
        {/* Mobile tabs */}
        <div className="flex border-b border-slate-200 mb-4 md:hidden">
          {(["doctor", "patient"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2.5 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? "text-clinical-600 border-b-2 border-clinical-500"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab === "doctor" ? "Doctor Report" : "Patient Report"}
            </button>
          ))}
        </div>

        {/* Desktop: side-by-side. Mobile: single active tab */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" style={{ minHeight: "520px" }}>
          <div className={activeTab === "patient" ? "hidden md:flex flex-col" : "flex flex-col"}>
            <ReportPanel
              title="Clinical Report"
              subtitle="Technical summary for care team"
              content={result.doctor_report}
              icon="doctor"
              accentClass="bg-clinical-50 text-clinical-800"
              downloadFilename="clinical-report"
            />
          </div>
          <div className={activeTab === "doctor" ? "hidden md:flex flex-col" : "flex flex-col"}>
            <ReportPanel
              title="Patient Summary"
              subtitle="Plain-language explanation for the patient"
              content={result.patient_report}
              icon="patient"
              accentClass="bg-teal-50 text-teal-800"
              downloadFilename="patient-summary"
            />
          </div>
        </div>
      </div>

      {/* Medications collapsible */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowMeds((v) => !v)}
          className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
        >
          <span>Medications ({result.medications.length})</span>
          {showMeds ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </button>
        {showMeds && (
          <div className="border-t border-slate-200">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50">
                  <th className="text-left px-5 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">Drug</th>
                  <th className="text-left px-5 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">Dose</th>
                  <th className="text-left px-5 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">Frequency</th>
                </tr>
              </thead>
              <tbody>
                {result.medications.map((m, i) => (
                  <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-5 py-3 font-medium text-slate-800">{m.name}</td>
                    <td className="px-5 py-3 text-slate-600">{m.dose || "—"}</td>
                    <td className="px-5 py-3 text-slate-600">{m.frequency || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {result.interactions.length > 0 && (
              <div className="border-t border-amber-200 bg-amber-50 px-5 py-4">
                <p className="text-xs font-semibold text-amber-700 mb-2">
                  Drug Interactions (OpenFDA)
                </p>
                <div className="space-y-2">
                  {result.interactions.map((i, idx) => (
                    <p key={idx} className="text-xs text-amber-800">
                      <strong>{i.drug}:</strong> {i.warnings.slice(0, 200)}…
                    </p>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Timeline collapsible */}
      {result.timeline_events.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <button
            onClick={() => setShowTimeline((v) => !v)}
            className="w-full flex items-center justify-between px-5 py-4 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
          >
            <span>Medical Timeline ({result.timeline_events.length} events)</span>
            {showTimeline ? (
              <ChevronUp className="w-4 h-4 text-slate-400" />
            ) : (
              <ChevronDown className="w-4 h-4 text-slate-400" />
            )}
          </button>
          {showTimeline && (
            <div className="border-t border-slate-200 divide-y divide-slate-100">
              {result.timeline_events.map((e, i) => (
                <div key={i} className="flex gap-4 px-5 py-3 hover:bg-slate-50">
                  <span className="text-xs text-slate-400 w-24 shrink-0 mt-0.5 font-mono">
                    {e.date}
                  </span>
                  <div>
                    <p className="text-sm text-slate-700">{e.event}</p>
                    <span className="text-xs text-slate-400 capitalize">{e.category}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Weave trace footer */}
      <div className="flex items-center justify-between bg-slate-100 rounded-xl px-5 py-3">
        <div>
          <p className="text-xs text-slate-500">
            W&B Weave audit trail
          </p>
          <p className="text-xs text-slate-400 font-mono mt-0.5">
            trace: {result.trace_id.slice(0, 16)}…
          </p>
        </div>
        <a
          href={result.weave_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-clinical-600 hover:text-clinical-700"
        >
          View W&B Weave
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}
