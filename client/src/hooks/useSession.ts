import { useEffect, useState } from "react";

/**
 * Drop-in useState replacement backed by sessionStorage instead of memory.
 * Used for the BYOK config so keys survive re-renders/navigation within a
 * tab but are gone the moment the tab closes - never persisted, never sent
 * anywhere except as request headers on API calls.
 */
export function useSession<T>(key: string, defaultValue: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const stored = sessionStorage.getItem(key);
      return stored !== null ? (JSON.parse(stored) as T) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // sessionStorage unavailable (private mode etc) - config just won't persist across renders
    }
  }, [key, value]);

  return [value, setValue];
}
