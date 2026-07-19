import { AlertOctagon, AlertTriangle, X } from "lucide-react";
import type { ToastItem } from "../hooks/useToast";

interface ToastStackProps {
  toasts: ToastItem[];
  onDismiss: (id: number) => void;
}

export default function ToastStack({ toasts, onDismiss }: ToastStackProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      role="region"
      aria-label="Notifications"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 w-80"
    >
      {toasts.map((t) => {
        const isError = t.tone === "error";
        return (
          <div
            key={t.id}
            role="alert"
            className={`flex gap-2.5 items-start rounded-lg border p-3 shadow-lg text-xs ${
              isError
                ? "bg-red-50 border-red-200 text-red-800"
                : "bg-amber-50 border-amber-200 text-amber-800"
            }`}
          >
            {isError ? (
              <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            ) : (
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" aria-hidden="true" />
            )}
            <div className="flex-1 min-w-0">
              <p className="font-semibold">{t.title}</p>
              {t.detail && (
                <p className="mt-0.5 opacity-90 break-words">{t.detail}</p>
              )}
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              aria-label="Dismiss notification"
              className="shrink-0 opacity-60 hover:opacity-100"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
