import { useCallback, useRef, useState } from "react";

export type ToastTone = "error" | "warning";

export interface ToastItem {
  id: number;
  tone: ToastTone;
  title: string;
  detail?: string;
}

const AUTO_DISMISS_MS = 8000;

export function useToast() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const push = useCallback((tone: ToastTone, title: string, detail?: string) => {
    const id = nextId.current++;
    setToasts((prev) => [...prev, { id, tone, title, detail }]);
    setTimeout(() => dismiss(id), AUTO_DISMISS_MS);
  }, [dismiss]);

  return { toasts, push, dismiss };
}
