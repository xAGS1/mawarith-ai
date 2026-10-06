"use client";
import { useEffect } from "react";
import type { AskResponse, ConceptContext } from "./types";
import { emptyAskState } from "./session-state";
import { useAskCoordinator } from "./ask-request-provider";

/** Session snapshots and pending requests share the existing surface key. */
export function useSessionAskState(storageKey: string) {
  const { entries, attach, update, start, cancel, clear } = useAskCoordinator();
  useEffect(() => attach(storageKey), [storageKey, attach]);
  const entry = entries.get(storageKey);
  return {
    ...(entry || emptyAskState()),
    initialized: Boolean(entry),
    pending: entry?.status === "pending",
    cancelled: entry?.status === "cancelled",
    restored: entry?.restored || false,
    startAsk: (question: string, context?: ConceptContext) =>
      start(storageKey, question, context),
    cancel: () => cancel(storageKey),
    clear: () => clear(storageKey),
    setQuestion: (value: string) => update(storageKey, "question", value),
    setSubmitted: (value: string) => update(storageKey, "submitted", value),
    setResult: (value: AskResponse | null) =>
      update(storageKey, "result", value),
    setError: (value: string | null) => update(storageKey, "error", value),
  };
}
