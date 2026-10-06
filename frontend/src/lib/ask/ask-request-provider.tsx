"use client";
import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { ask, AskError } from "./client";
import type { ConceptContext } from "./types";
import {
  emptyAskState,
  readAskSession,
  writeAskSession,
  type AskSessionState,
} from "./session-state";

type Entry = AskSessionState & {
  status: "idle" | "pending" | "success" | "error" | "cancelled";
  restored: boolean;
  controller?: AbortController;
};
type Coordinator = {
  entries: Map<string, Entry>;
  revision: number;
  attach: (key: string) => () => void;
  update: <K extends keyof AskSessionState>(
    key: string,
    field: K,
    value: AskSessionState[K],
  ) => void;
  start: (key: string, question: string, context?: ConceptContext) => void;
  cancel: (key: string) => void;
  clear: (key: string) => void;
};
const Context = createContext<Coordinator | null>(null);

/** Owns requests across client navigation; no shared surface lock. */
export function AskRequestProvider({ children }: { children: ReactNode }) {
  const entries = useRef(new Map<string, Entry>());
  const subscribers = useRef(new Map<string, number>());
  const [revision, setRevision] = useState(0);
  const notify = useCallback(() => setRevision((value) => value + 1), []);
  const ensure = useCallback((key: string) => {
    let entry = entries.current.get(key);
    if (!entry) {
      const state = readAskSession(key);
      entry = {
        ...state,
        status: "idle",
        restored: Boolean(state.submitted || state.result || state.error),
      };
      entries.current.set(key, entry);
    }
    return entry;
  }, []);
  const save = useCallback((key: string, entry: Entry) => {
    const { question, submitted, result, error } = entry;
    writeAskSession(key, { question, submitted, result, error });
  }, []);
  const attach = useCallback(
    (key: string) => {
      ensure(key);
      subscribers.current.set(key, (subscribers.current.get(key) || 0) + 1);
      notify();
      return () => {
        const count = (subscribers.current.get(key) || 1) - 1;
        if (count) subscribers.current.set(key, count);
        else {
          subscribers.current.delete(key);
          if (entries.current.get(key)?.status !== "pending")
            entries.current.delete(key);
        }
      };
    },
    [ensure, notify],
  );
  const update = useCallback(
    <K extends keyof AskSessionState>(
      key: string,
      field: K,
      value: AskSessionState[K],
    ) => {
      const entry = ensure(key);
      Object.assign(entry, { [field]: value });
      save(key, entry);
      notify();
    },
    [ensure, save, notify],
  );
  const start = useCallback(
    (key: string, question: string, context?: ConceptContext) => {
      const entry = ensure(key);
      if (entry.status === "pending") return;
      const trimmed = question.trim();
      if (!trimmed) {
        update(key, "error", "empty");
        return;
      }
      const controller = new AbortController();
      Object.assign(entry, {
        question: entry.question.trim() === trimmed ? entry.question : question,
        submitted: trimmed,
        status: "pending",
        error: null,
        controller,
        restored: false,
      });
      save(key, entry);
      notify();
      void ask(trimmed, context, controller.signal)
        .then((result) => {
          if (entry.controller !== controller) return;
          entry.result = result;
          entry.status = "success";
        })
        .catch((error: unknown) => {
          if (entry.controller !== controller) return;
          entry.error =
            error instanceof AskError ? error.code : "request_error";
          entry.status = "error";
        })
        .finally(() => {
          if (entry.controller !== controller) return;
          delete entry.controller;
          save(key, entry);
          // Detached terminal entries remain in sessionStorage, not the Map.
          if (!subscribers.current.has(key)) entries.current.delete(key);
          notify();
        });
    },
    [ensure, update, save, notify],
  );
  const cancel = useCallback(
    (key: string) => {
      const entry = entries.current.get(key);
      if (entry?.status !== "pending") return;
      entry.controller?.abort();
      delete entry.controller;
      entry.status = "cancelled";
      entry.error = null;
      save(key, entry);
      notify();
    },
    [save, notify],
  );
  const clear = useCallback(
    (key: string) => {
      const entry = ensure(key);
      if (entry.status === "pending") return;
      Object.assign(entry, emptyAskState(), {
        status: "idle",
        restored: false,
      });
      try {
        sessionStorage.removeItem(key);
      } catch {
        /* Storage may be unavailable. */
      }
      notify();
    },
    [ensure, notify],
  );
  const value = useMemo(
    () => ({
      entries: entries.current,
      revision,
      attach,
      update,
      start,
      cancel,
      clear,
    }),
    [revision, attach, update, start, cancel, clear],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useAskCoordinator() {
  const value = useContext(Context);
  if (!value) throw new Error("Ask surfaces require AskRequestProvider");
  return value;
}
