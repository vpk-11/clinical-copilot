import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload, FileText, X, CheckCircle2, Loader2, AlertCircle, ChevronRight, ChevronDown, ChevronUp, Download, Copy, Check, FolderDown,
} from "lucide-react";
import { uploadFile, normalizeText, listSamples, sampleDownloadUrl, sampleZipUrl } from "../api";
import type { SampleGroup } from "../api";
import type { LLMConfig } from "../types";

function extOf(filename: string): string {
  return filename.split(".").pop()?.toUpperCase() ?? "";
}

function docKind(filename: string): string {
  // "chf-jane-doe__discharge-summary.docx" -> "discharge summary"
  const doc = filename.split("__")[1] ?? filename;
  return doc.replace(/\.[^.]+$/, "").replace(/-/g, " ");
}

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  // .doc (Word 97-2003 binary) is excluded - python-docx cannot parse it
  "text/markdown": [".md"],
  "text/plain": [".txt"],
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface FileEntry {
  id: string;
  file: File;
  status: "pending" | "extracting" | "ready" | "error";
  text: string;
  error?: string;
}

interface FileUploadProps {
  patientId: string;
  onPatientIdChange: (id: string) => void;
  onReady: (combinedText: string, filenames: string[]) => void;
  llmConfig?: LLMConfig;
}

export default function FileUpload({ patientId, onPatientIdChange, onReady, llmConfig }: FileUploadProps) {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [normalizing, setNormalizing] = useState(false);
  const [normalizeError, setNormalizeError] = useState("");
  const [sampleGroups, setSampleGroups] = useState<SampleGroup[]>([]);
  const [copiedId, setCopiedId] = useState("");
  const [samplesOpen, setSamplesOpen] = useState(false);

  useEffect(() => {
    listSamples()
      .then((res) => setSampleGroups(res.groups))
      .catch(() => setSampleGroups([]));
  }, []);

  const copyDemoId = useCallback((demoId: string) => {
    navigator.clipboard?.writeText(demoId).then(() => {
      setCopiedId(demoId);
      setTimeout(() => setCopiedId((current) => (current === demoId ? "" : current)), 1500);
    });
  }, []);

  const extractFile = useCallback(async (entry: FileEntry) => {
    setFiles((prev) =>
      prev.map((f) => (f.id === entry.id ? { ...f, status: "extracting" } : f))
    );
    try {
      const result = await uploadFile(entry.file);
      setFiles((prev) =>
        prev.map((f) =>
          f.id === entry.id ? { ...f, status: "ready", text: result.text } : f
        )
      );
    } catch (e) {
      setFiles((prev) =>
        prev.map((f) =>
          f.id === entry.id
            ? { ...f, status: "error", error: (e as Error).message }
            : f
        )
      );
    }
  }, []);

  const handleDrop = useCallback(
    (accepted: File[]) => {
      const newEntries: FileEntry[] = accepted.map((file) => ({
        id: `${file.name}-${file.size}-${Date.now()}`,
        file,
        status: "pending" as const,
        text: "",
      }));

      setFiles((prev) => {
        const existing = new Set(
          prev.map((f) => `${f.file.name}-${f.file.size}-${f.file.lastModified}`)
        );
        const fresh = newEntries.filter(
          (e) => !existing.has(`${e.file.name}-${e.file.size}-${e.file.lastModified}`)
        );
        return [...prev, ...fresh];
      });

      // Start extraction immediately for each new file
      newEntries.forEach((entry) => extractFile(entry));
    },
    [extractFile]
  );

  const removeFile = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  const handleSend = useCallback(async () => {
    const readyFiles = files.filter((f) => f.status === "ready");
    if (readyFiles.length === 0) return;

    setNormalizing(true);
    setNormalizeError("");

    try {
      const combined = readyFiles
        .map((f) => `[SOURCE: ${f.file.name}]\n${f.text}`)
        .join("\n\n---\n\n");

      const result = await normalizeText(combined, patientId, llmConfig);
      onReady(result.normalized_text, readyFiles.map((f) => f.file.name));
    } catch (e) {
      setNormalizeError((e as Error).message);
    } finally {
      setNormalizing(false);
    }
  }, [files, patientId, onReady, llmConfig]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: ACCEPTED_TYPES,
    maxSize: 10 * 1024 * 1024,
    onDropAccepted: handleDrop,
    onDropRejected: (rejections) => {
      rejections.forEach((r) => {
        const msg =
          r.errors[0]?.code === "file-too-large"
            ? `${r.file.name}: too large (max 10 MB)`
            : r.errors[0]?.code === "file-invalid-type"
            ? `${r.file.name}: unsupported type`
            : r.errors[0]?.message ?? "Upload failed";
        setNormalizeError(msg);
      });
    },
  });

  const readyCount = files.filter((f) => f.status === "ready").length;
  const processingCount = files.filter((f) => f.status === "extracting").length;
  const canSend = readyCount > 0 && processingCount === 0 && !normalizing;

  return (
    <div className="space-y-4">
      {/* Patient ID */}
      <div className="flex items-center gap-3">
        <label htmlFor="patient-id" className="text-sm font-medium text-slate-600 whitespace-nowrap">
          Patient ID
        </label>
        <input
          id="patient-id"
          type="text"
          value={patientId}
          onChange={(e) => onPatientIdChange(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-800 w-40 focus:outline-none focus:ring-2 focus:ring-clinical-500 focus:border-transparent"
          placeholder="DEMO-001"
          disabled={normalizing}
          aria-describedby="patient-id-hint"
        />
        <span id="patient-id-hint" className="text-xs text-slate-400">
          Your own tracking label - unrelated to the name/MRN inside the chart
        </span>
      </div>

      {/* Sample charts - synthetic data, grouped one bundle per patient.
          Each bundle's demo ID is also printed inside every file in it, so
          whichever document gets opened first still tells you what to type
          into Patient ID above. */}
      {sampleGroups.length > 0 && (
        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
          <button
            onClick={() => setSamplesOpen((v) => !v)}
            aria-expanded={samplesOpen}
            aria-controls="sample-patients-panel"
            className="w-full flex items-center justify-between px-4 py-2.5 border-b border-slate-200 bg-slate-50 hover:bg-slate-100 transition-colors"
          >
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
              No file handy? Try a sample patient
            </span>
            {samplesOpen ? (
              <ChevronUp className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" aria-hidden="true" />
            )}
          </button>
          {samplesOpen && (
          <ul id="sample-patients-panel" className="divide-y divide-slate-100">
            {sampleGroups.map((group) => (
              <li key={group.group} className="flex items-center gap-3 px-4 py-2.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-800">{group.label}</span>
                    <span className="text-xs text-slate-400">&middot; {group.patient}</span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                    <button
                      onClick={() => copyDemoId(group.demo_id)}
                      title="Copy Demo ID"
                      aria-label={`Copy Demo ID ${group.demo_id} for ${group.patient}`}
                      className="inline-flex items-center gap-1 text-xs font-mono text-clinical-700 bg-clinical-50 hover:bg-clinical-100 border border-clinical-100 rounded px-1.5 py-0.5 transition-colors"
                    >
                      {copiedId === group.demo_id ? (
                        <Check className="w-3 h-3" aria-hidden="true" />
                      ) : (
                        <Copy className="w-3 h-3" aria-hidden="true" />
                      )}
                      {group.demo_id}
                    </button>
                    {group.files.map((filename) => (
                      <a
                        key={filename}
                        href={sampleDownloadUrl(filename)}
                        download={filename}
                        title={docKind(filename)}
                        aria-label={`Download ${docKind(filename)} (${extOf(filename)}) for ${group.patient}`}
                        className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-clinical-700 bg-slate-100 hover:bg-clinical-50 rounded px-1.5 py-0.5 border border-slate-200 hover:border-clinical-200 transition-colors"
                      >
                        <Download className="w-3 h-3" aria-hidden="true" />
                        {extOf(filename)}
                      </a>
                    ))}
                  </div>
                </div>
                <a
                  href={sampleZipUrl(group.group)}
                  download={`${group.group}.zip`}
                  aria-label={`Download all files for ${group.patient} as zip`}
                  className="shrink-0 inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-clinical-500 hover:bg-clinical-600 rounded-lg px-3 py-1.5 transition-colors"
                >
                  <FolderDown className="w-3.5 h-3.5" aria-hidden="true" />
                  Download all
                </a>
              </li>
            ))}
          </ul>
          )}
        </div>
      )}

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all
          ${normalizing ? "pointer-events-none opacity-60" : ""}
          ${isDragActive
            ? "border-clinical-500 bg-clinical-50"
            : "border-slate-300 bg-white hover:border-clinical-400 hover:bg-clinical-50"
          }
        `}
      >
        <input {...getInputProps()} aria-label="Upload clinical documents" />
        <div className="flex flex-col items-center gap-3">
          <div className="p-3 bg-clinical-50 rounded-full">
            <Upload className="w-6 h-6 text-clinical-500" aria-hidden="true" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-700">
              {isDragActive ? "Drop files here" : "Drop clinical documents here"}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              or click to browse - PDF, DOCX, MD, TXT
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {(["PDF", "DOCX", "MD", "TXT"] as const).map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-medium rounded border border-slate-200"
              >
                {t}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-400">
            Upload multiple files - radiology reports, lab results, clinical notes
          </p>
        </div>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
          <div className="px-4 py-2.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">
              Files ({files.length})
            </span>
            {readyCount > 0 && (
              <span role="status" aria-live="polite" className="text-xs text-green-600 font-medium">
                {readyCount} ready
                {processingCount > 0 ? `, ${processingCount} processing` : ""}
              </span>
            )}
          </div>

          <ul className="divide-y divide-slate-100">
            {files.map((entry) => (
              <li
                key={entry.id}
                className="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors group"
              >
                {/* Icon */}
                <div className="shrink-0">
                  {entry.status === "extracting" ? (
                    <Loader2 className="w-4 h-4 text-clinical-500 animate-spin" aria-hidden="true" />
                  ) : entry.status === "ready" ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" aria-hidden="true" />
                  ) : entry.status === "error" ? (
                    <AlertCircle className="w-4 h-4 text-red-500" aria-hidden="true" />
                  ) : (
                    <FileText className="w-4 h-4 text-slate-400" aria-hidden="true" />
                  )}
                </div>

                {/* Name + meta */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {entry.file.name}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {formatBytes(entry.file.size)}
                    {entry.status === "extracting" && " - extracting text..."}
                    {entry.status === "ready" &&
                      entry.text &&
                      ` - ${entry.text.length.toLocaleString()} chars`}
                    {entry.status === "error" && (
                      <span className="text-red-500"> - {entry.error}</span>
                    )}
                  </p>
                </div>

                {/* Remove */}
                <button
                  onClick={() => removeFile(entry.id)}
                  disabled={normalizing}
                  className="shrink-0 p-1 rounded text-slate-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  title="Remove file"
                  aria-label={`Remove ${entry.file.name}`}
                >
                  <X className="w-3.5 h-3.5" aria-hidden="true" />
                </button>
              </li>
            ))}
          </ul>

          {/* Send button */}
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
            {normalizeError && (
              <p role="alert" className="text-xs text-red-600 flex-1">{normalizeError}</p>
            )}
            <div className="flex-1" />
            {processingCount > 0 && (
              <span role="status" className="text-xs text-slate-500">
                Waiting for {processingCount} file{processingCount > 1 ? "s" : ""}...
              </span>
            )}
            <button
              onClick={handleSend}
              disabled={!canSend}
              className={`
                inline-flex items-center gap-2 text-sm font-semibold px-5 py-2 rounded-lg transition-colors
                ${canSend
                  ? "bg-clinical-500 hover:bg-clinical-600 text-white shadow-sm"
                  : "bg-slate-200 text-slate-400 cursor-not-allowed"
                }
              `}
            >
              {normalizing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Normalizing...
                </>
              ) : (
                <>
                  Send to InputAgent
                  <ChevronRight className="w-4 h-4" aria-hidden="true" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
