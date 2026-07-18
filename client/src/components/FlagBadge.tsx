import type { RiskFlag } from "../types";

interface FlagBadgeProps {
  flag: RiskFlag;
  showEvidence?: boolean;
}

const SEVERITY_STYLES = {
  HIGH: "bg-red-50 text-red-700 border-red-200 ring-red-100",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200 ring-amber-100",
  LOW: "bg-green-50 text-green-700 border-green-200 ring-green-100",
};

const SEVERITY_DOT = {
  HIGH: "bg-red-500",
  MEDIUM: "bg-amber-500",
  LOW: "bg-green-500",
};

export default function FlagBadge({ flag, showEvidence = false }: FlagBadgeProps) {
  const sev = flag.severity ?? "LOW";
  const styles = SEVERITY_STYLES[sev] ?? SEVERITY_STYLES.LOW;
  const dot = SEVERITY_DOT[sev] ?? SEVERITY_DOT.LOW;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ring-1 ${styles}`}
      title={flag.evidence ?? flag.flag}
    >
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dot}`} aria-hidden="true" />
      <span className="sr-only">{sev} severity: </span>
      {flag.flag}
      {showEvidence && flag.evidence && (
        <span className="font-normal opacity-75 ml-0.5">- {flag.evidence}</span>
      )}
    </span>
  );
}
