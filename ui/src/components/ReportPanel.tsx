import { useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Stethoscope, User, Download } from "lucide-react";

interface ReportPanelProps {
  title: string;
  subtitle: string;
  content: string;
  icon: "doctor" | "patient";
  accentClass: string;
  downloadFilename: string;
}

const PRINT_CSS = `
  body { font-family: Georgia, 'Times New Roman', serif; font-size: 11pt; line-height: 1.65;
         max-width: 720px; margin: 0 auto; padding: 24px 32px; color: #111; }
  h1 { font-size: 20pt; font-weight: bold; margin: 0 0 6px; }
  h2 { font-size: 13pt; font-weight: bold; border-bottom: 1px solid #ccc;
       padding-bottom: 3px; margin: 20px 0 8px; }
  h3 { font-size: 11pt; font-weight: bold; margin: 14px 0 5px; }
  p  { margin: 5px 0 10px; }
  ul, ol { margin: 4px 0 10px; padding-left: 22px; }
  li { margin-bottom: 4px; }
  strong { font-weight: 700; }
  em { font-style: italic; }
  hr { border: none; border-top: 1px solid #ddd; margin: 14px 0; }
  table { width: 100%; border-collapse: collapse; font-size: 10pt; margin: 8px 0 14px; }
  thead tr { background: #f0f0f0; }
  th { text-align: left; padding: 5px 8px; border: 1px solid #bbb;
       font-size: 9pt; text-transform: uppercase; letter-spacing: 0.04em; font-family: Arial, sans-serif; }
  td { padding: 5px 8px; border: 1px solid #ddd; vertical-align: top; }
  tr:nth-child(even) td { background: #fafafa; }
  code { font-family: 'Courier New', monospace; font-size: 9pt;
         background: #f5f5f5; padding: 1px 4px; border-radius: 2px; }
  blockquote { border-left: 3px solid #bbb; padding-left: 12px; margin: 8px 0;
               color: #555; font-style: italic; }
  @media print {
    @page { margin: 18mm 20mm; size: A4; }
    body { padding: 0; }
  }
`;

export default function ReportPanel({
  title,
  subtitle,
  content,
  icon,
  accentClass,
  downloadFilename: _downloadFilename,
}: ReportPanelProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownloadPDF = () => {
    if (!contentRef.current) return;
    const html = contentRef.current.innerHTML;

    const win = window.open("", "_blank");
    if (!win) return;

    win.document.write(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>${title}</title>
  <style>${PRINT_CSS}</style>
</head>
<body>${html}</body>
</html>`);
    win.document.close();
    // Small delay ensures CSS is applied before print dialog opens
    setTimeout(() => {
      win.focus();
      win.print();
    }, 350);
  };

  return (
    <div className="flex flex-col bg-white border border-slate-200 rounded-xl overflow-hidden h-full">
      {/* Header */}
      <div className={`px-5 py-3.5 border-b border-slate-200 ${accentClass}`}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2.5">
            {icon === "doctor" ? (
              <Stethoscope className="w-4 h-4 shrink-0" />
            ) : (
              <User className="w-4 h-4 shrink-0" />
            )}
            <div>
              <h3 className="text-sm font-semibold">{title}</h3>
              <p className="text-xs opacity-70 mt-0.5">{subtitle}</p>
            </div>
          </div>
          <button
            onClick={handleDownloadPDF}
            className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg bg-white/60 hover:bg-white/90 transition-colors border border-current/20"
            title={`Download ${title} as PDF`}
          >
            <Download className="w-3 h-3" />
            PDF
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-5">
        <div className="report-content" ref={contentRef}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
