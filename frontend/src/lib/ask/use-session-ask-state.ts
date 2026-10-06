"use client";
import { useEffect, useRef, useState } from "react";
import { isRecord, type AskResponse } from "./types";
type State = {
  question: string;
  submitted: string;
  result: AskResponse | null;
  error: string | null;
};
const empty = (): State => ({
  question: "",
  submitted: "",
  result: null,
  error: null,
});
const errors = ["empty", "timeout", "backend_unavailable", "request_error"];
function validResult(value: unknown): value is AskResponse {
  if (
    !isRecord(value) ||
    typeof value.answer !== "string" ||
    typeof value.mode !== "string" ||
    !["learn", "case"].includes(value.mode) ||
    typeof value.language !== "string" ||
    !["ar", "en"].includes(value.language) ||
    typeof value.decision_state !== "string" ||
    ![
      "ready",
      "needs_clarification",
      "specialist_referral",
      "out_of_scope",
    ].includes(value.decision_state)
  )
    return false;
  return (
    (value.clarification_question == null ||
      typeof value.clarification_question === "string") &&
    (value.case_details == null || isRecord(value.case_details)) &&
    (value.evidence_status == null ||
      ["supported", "insufficient"].includes(String(value.evidence_status))) &&
    ["sources", "source_excerpts"].every(
      (key) =>
        value[key] == null ||
        (Array.isArray(value[key]) && value[key].every(isRecord)),
    ) &&
    (value.limitations == null ||
      (Array.isArray(value.limitations) &&
        value.limitations.every((item) => typeof item === "string"))) &&
    (value.key_concepts == null ||
      (Array.isArray(value.key_concepts) &&
        value.key_concepts.every(
          (item) =>
            isRecord(item) &&
            typeof item.term === "string" &&
            typeof item.explanation === "string",
        )))
  );
}

/** Stores durable UI data only. Requests, loading and controllers remain local. */
export function useSessionAskState(storageKey: string) {
  const [state, setState] = useState<State>(empty);
  const current = useRef<State>(empty());
  const restoredKey = useRef<string | null>(null);
  const [initialized, setInitialized] = useState(false);
  useEffect(() => {
    let restored = empty();
    try {
      const raw = sessionStorage.getItem(storageKey);
      const value: unknown =
        raw && raw.length < 2_000_000 ? JSON.parse(raw) : null;
      if (
        isRecord(value) &&
        value.version === 1 &&
        typeof value.question === "string" &&
        value.question.length <= 2000 &&
        typeof value.submitted === "string" &&
        value.submitted.length <= 2000 &&
        (value.result === null || validResult(value.result)) &&
        (value.error === null ||
          (typeof value.error === "string" && errors.includes(value.error)))
      ) {
        restored = {
          question: value.question,
          submitted: value.submitted,
          result: value.result as AskResponse | null,
          error: value.error as string | null,
        };
      } else if (raw) sessionStorage.removeItem(storageKey);
    } catch {
      /* Unavailable or corrupt storage must not prevent asking. */
    }
    current.current = restored;
    restoredKey.current = storageKey;
    setState(restored);
    setInitialized(true);
  }, [storageKey]);
  function update<K extends keyof State>(key: K, value: State[K]) {
    // The restoration effect runs before caller mount effects (e.g. URL prefill).
    // Never let an early input event overwrite a snapshot before that read.
    if (restoredKey.current !== storageKey) return;
    const next = { ...current.current, [key]: value };
    current.current = next;
    setState(next);
    try {
      sessionStorage.setItem(
        storageKey,
        JSON.stringify({
          version: 1,
          ...next,
          error: next.error === "busy" ? null : next.error,
        }),
      );
    } catch {
      /* Best effort, including quota limits. */
    }
  }
  function clear() {
    if (restoredKey.current !== storageKey) return;
    current.current = empty();
    setState(current.current);
    try {
      sessionStorage.removeItem(storageKey);
    } catch {
      /* Storage may be blocked. */
    }
  }
  return {
    ...state,
    initialized,
    clear,
    setQuestion: (value: string) => update("question", value),
    setSubmitted: (value: string) => update("submitted", value),
    setResult: (value: AskResponse | null) => update("result", value),
    setError: (value: string | null) => update("error", value),
  };
}
