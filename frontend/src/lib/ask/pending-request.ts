import { inferMode } from "./infer-mode";
import { isRecord, type AskMode } from "./types";

export const PENDING_REQUEST_KEY = "mawarith-ask-pending";
export const PENDING_MAX_AGE = 3 * 60_000;
export interface PendingRequest {
  status: "pending";
  question: string;
  mode: AskMode;
  startedAt: number;
}
export function readPendingRequest(): PendingRequest | null {
  try {
    const raw = sessionStorage.getItem(PENDING_REQUEST_KEY);
    if (!raw) return null;
    const value: unknown = JSON.parse(raw);
    if (
      isRecord(value) &&
      value.status === "pending" &&
      typeof value.question === "string" &&
      value.question.trim() &&
      ["learn", "case"].includes(String(value.mode)) &&
      typeof value.startedAt === "number" &&
      Number.isFinite(value.startedAt) &&
      value.startedAt > 0 &&
      value.startedAt <= Date.now()
    )
      return value as unknown as PendingRequest;
    sessionStorage.removeItem(PENDING_REQUEST_KEY);
  } catch {
    /* Storage may be blocked; retain in-memory duplicate protection. */
  }
  return null;
}
export function markPendingRequest(question: string): PendingRequest {
  const marker: PendingRequest = {
    status: "pending",
    question,
    mode: inferMode(question),
    startedAt: Date.now(),
  };
  try {
    sessionStorage.setItem(PENDING_REQUEST_KEY, JSON.stringify(marker));
  } catch {
    /* Best effort when storage is unavailable. */
  }
  return marker;
}
export function clearPendingRequest(marker: PendingRequest): void {
  try {
    const current = readPendingRequest();
    if (
      current?.startedAt === marker.startedAt &&
      current.question === marker.question &&
      current.mode === marker.mode
    )
      sessionStorage.removeItem(PENDING_REQUEST_KEY);
  } catch {
    /* Storage may be unavailable. */
  }
}
