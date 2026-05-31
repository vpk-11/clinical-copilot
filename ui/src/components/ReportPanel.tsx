import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Stethoscope, User } from "lucide-react";

interface ReportPanelProps {
  title: string;
  subtitle: string;
  content: string;
  icon: "doctor" | "patient";
  accentClass: string;
}

export default function ReportPanel({
  title,
  subtitle,
  content,
  icon,
  accentClass,
}: ReportPanelProps) {
  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden h-full">
      {/* Header */}
      <div className={`px-5 py-4 border-b border-slate-200 ${accentClass}`}>
        <div className="flex items-center gap-2.5">
          {icon === "doctor" ? (
            <Stethoscope className="w-4 h-4 shrink-0" />
          ) : (
            <User className="w-4 h-4 shrink-0" />
          )}
          <div>
            <h3 className="text-sm font-semibold">{title}</h3>
            <p className="text-xs opacity-75 mt-0.5">{subtitle}</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="report-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
