import { isRecord, type AskResponse, type ConceptContext } from "./types";
import { inferMode } from "./infer-mode";
export class AskError extends Error {
  constructor(
    public code:
      | "timeout"
      | "backend_unavailable"
      | "request_error"
      | "busy"
      | "cancelled",
    public status?: number,
  ) {
    super(code);
  }
}
export async function ask(
  question: string,
  conceptContext?: ConceptContext,
  signal?: AbortSignal,
): Promise<AskResponse> {
  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: conceptContext ? "learn" : inferMode(question),
        question,
        ...(conceptContext ? { concept_context: conceptContext } : {}),
      }),
      signal: signal
        ? AbortSignal.any([signal, AbortSignal.timeout(125_000)])
        : AbortSignal.timeout(125_000),
    });
    const data: unknown = await response.json();
    if (!response.ok) {
      const code =
        isRecord(data) && isRecord(data.error) ? data.error.code : undefined;
      throw new AskError(
        response.status === 429 ||
          code === "busy" ||
          code === "temporarily_busy"
          ? "busy"
          : code === "timeout" || response.status === 504
            ? "timeout"
            : code === "backend_unavailable" || response.status === 503
              ? "backend_unavailable"
              : "request_error",
        response.status,
      );
    }
    if (
      !isRecord(data) ||
      typeof data.answer !== "string" ||
      !["learn", "case"].includes(String(data.mode)) ||
      !["ar", "en"].includes(String(data.language)) ||
      ![
        "ready",
        "needs_clarification",
        "specialist_referral",
        "out_of_scope",
      ].includes(String(data.decision_state))
    )
      throw new AskError("request_error");
    return data as unknown as AskResponse;
  } catch (error) {
    if (signal?.aborted) throw new AskError("cancelled");
    if (error instanceof AskError) throw error;
    if (
      error instanceof Error &&
      ["TimeoutError", "AbortError"].includes(error.name)
    )
      throw new AskError("timeout");
    throw new AskError("request_error");
  }
}
