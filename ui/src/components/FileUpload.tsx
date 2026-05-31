import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { FileText, Upload, AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { uploadFile, normalizeText } from "../api";

const ACCEPTED_TYPES = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/msword": [".doc"],
  "text/markdown": [".md"],
  "text/plain": [".txt"],
};

interface FileUploadProps {
  patientId: string;
  onPatientIdChange: (id: string) => void;
  onReady: (normalizedText: string, filename: string) => void;
}

type UploadState =
  | { status: "idle" }
  | { status: "extracting"; filename: string }
  | { status: "normalizing"; filename: string }
  | { status: "done"; filename: string; charCount: number }
  | { status: "error"; message: string };

export default function FileUpload({ patientId, onPatientIdChange, onReady }: FileUploadProps) {
  const [state, setState] = useState<UploadState>({ status: "idle" });

  const handleFile = useCallback(
    async (file: File) => {
      setState({ status: "extracting", filename: file.name });

      try {
        const extracted = await uploadFile(file);
        setState({ status: "normalizing", filename: file.name });

        const normalized = await normalizeText(extracted.text, patientId);
        setState({
          status: "done",
          filename: file.name,
          charCount: normalized.normalized_char_count,
        });
        onReady(normalized.normalized_text, file.name);
      } catch (e) {
        setState({ status: "error", message: (e as Error).message });
      }
    },
    [patientId, onReady]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    onDropAccepted: ([file]) => handleFile(file),
    onDropRejected: ([rejection]) => {
      const msg =
        rejection.errors[0]?.code === "file-too-large"
          ? "File too large. Maximum 10 MB."
          : rejection.errors[0]?.code === "file-invalid-type"
          ? "Unsupported file type. Upload a PDF, DOCX, MD, or TXT file."
          : rejection.errors[0]?.message ?? "Upload failed.";
      setState({ status: "error", message: msg });
    },
  });

  const isProcessing =
    state.status === "extracting" || state.status === "normalizing";

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
          disabled={isProcessing}
        />
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all
          ${isProcessing ? "pointer-events-none opacity-60" : ""}
          ${isDragActive
            ? "border-clinical-500 bg-clinical-50"
            : state.status === "error"
            ? "border-red-300 bg-red-50 hover:border-red-400"
            : state.status === "done"
            ? "border-green-300 bg-green-50 hover:border-green-400"
            : "border-slate-300 bg-white hover:border-clinical-400 hover:bg-clinical-50"
          }
        `}
      >
        <input {...getInputProps()} />

        {isProcessing ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="w-10 h-10 text-clinical-500 animate-spin" />
            <p className="text-sm font-medium text-clinical-700">
              {state.status === "extracting"
                ? `Extracting text from ${(state as { filename: string }).filename}...`
                : "Normalizing clinical content..."}
            </p>
            <p className="text-xs text-slate-500">
              {state.status === "normalizing" &&
                "InputAgent is structuring the chart into a standardized format"}
            </p>
          </div>
        ) : state.status === "done" ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle2 className="w-10 h-10 text-green-500" />
            <p className="text-sm font-medium text-green-700">
              {(state as { filename: string }).filename} — ready
            </p>
            <p className="text-xs text-slate-500">
              {(state as { charCount: number }).charCount.toLocaleString()} characters extracted and normalized
            </p>
            <p className="text-xs text-clinical-600 underline cursor-pointer">
              Upload a different file
            </p>
          </div>
        ) : state.status === "error" ? (
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="w-10 h-10 text-red-500" />
            <p className="text-sm font-medium text-red-700">{(state as { message: string }).message}</p>
            <p className="text-xs text-slate-500">Click or drop a file to try again</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="p-4 bg-clinical-50 rounded-full">
              <Upload className="w-8 h-8 text-clinical-500" />
            </div>
            <div>
              <p className="text-base font-semibold text-slate-700">
                {isDragActive ? "Drop the file here" : "Drop a clinical document here"}
              </p>
              <p className="text-sm text-slate-500 mt-1">or click to browse</p>
            </div>
            <div className="flex items-center gap-2">
              {["PDF", "DOCX", "MD", "TXT"].map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-100 text-slate-600 text-xs font-medium rounded-full border border-slate-200"
                >
                  <FileText className="w-3 h-3" />
                  {t}
                </span>
              ))}
            </div>
            <p className="text-xs text-slate-400">
              PDFs with X-rays, ECGs, and lab reports are supported — captions and footnotes are extracted
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
