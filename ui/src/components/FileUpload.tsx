import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload, FileText, X, CheckCircle2, Loader2, AlertCircle, ChevronRight,
} from "lucide-react";
import { uploadFile, normalizeText } from "../api";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/msword": [".doc"],
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
}

export default function FileUpload({ patientId, onPatientIdChange, onReady }: FileUploadProps) {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [normalizing, setNormalizing] = useState(false);
  const [normalizeError, setNormalizeError] = useState("");

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
        // Deduplicate by name+size
        const existing = new Set(prev.map((f) => `${f.file.name}-${f.file.size}`));
        const fresh = newEntries.filter(
          (e) => !existing.has(`${e.file.name}-${e.file.size}`)
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

      const result = await normalizeText(combined, patientId);
      onReady(result.normalized_text, readyFiles.map((f) => f.file.name));
    } catch (e) {
      setNormalizeError((e as Error).message);
    } finally {
      setNormalizing(false);
    }
  }, [files, patientId, onReady]);

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
        <label className="text-sm font-medium text-slate-600 whitespace-nowrap">
          Patient ID
        </label>
        <input
          type="text"
          value={patientId}
          onChange={(e) => onPatientIdChange(e.target.value)}
          className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm text-slate-800 w-40 focus:outline-none focus:ring-2 focus:ring-clinical-500 focus:border-transparent"
          placeholder="DEMO-001"
          disabled={normalizing}
        />
      </div>

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
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div className="p-3 bg-clinical-50 rounded-full">
            <Upload className="w-6 h-6 text-clinical-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-700">
              {isDragActive ? "Drop files here" : "Drop clinical documents here"}
            </p>
            <p className="text-xs text-slate-500 mt-0.5">
              or click to browse — PDF, DOCX, MD, TXT
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {["PDF", "DOCX", "MD", "TXT"].map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 bg-slate-100 text-slate-500 text-xs font-medium rounded border border-slate-200"
              >
                {t}
              </span>
            ))}
          </div>
          <p className="text-xs text-slate-400">
            Upload multiple files — radiology reports, lab results, clinical notes
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
              <span className="text-xs text-green-600 font-medium">
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
                    <Loader2 className="w-4 h-4 text-clinical-500 animate-spin" />
                  ) : entry.status === "ready" ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : entry.status === "error" ? (
                    <AlertCircle className="w-4 h-4 text-red-500" />
                  ) : (
                    <FileText className="w-4 h-4 text-slate-400" />
                  )}
                </div>

                {/* Name + meta */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate">
                    {entry.file.name}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {formatBytes(entry.file.size)}
                    {entry.status === "extracting" && " — extracting text..."}
                    {entry.status === "ready" &&
                      entry.text &&
                      ` — ${entry.text.length.toLocaleString()} chars`}
                    {entry.status === "error" && (
                      <span className="text-red-500"> — {entry.error}</span>
                    )}
                  </p>
                </div>

                {/* Remove */}
                <button
                  onClick={() => removeFile(entry.id)}
                  disabled={normalizing}
                  className="shrink-0 p-1 rounded text-slate-300 hover:text-red-500 hover:bg-red-50 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                  title="Remove file"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
          </ul>

          {/* Send button */}
          <div className="px-4 py-3 border-t border-slate-200 bg-slate-50 flex items-center justify-between gap-3">
            {normalizeError && (
              <p className="text-xs text-red-600 flex-1">{normalizeError}</p>
            )}
            <div className="flex-1" />
            {processingCount > 0 && (
              <span className="text-xs text-slate-500">
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
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Normalizing...
                </>
              ) : (
                <>
                  Send to InputAgent
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
