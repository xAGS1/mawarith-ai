export type AskMode = "learn" | "case";
export type ConceptContext = { slug: string; title: string };
export type DecisionState =
  "ready" | "needs_clarification" | "specialist_referral" | "out_of_scope";
export type SourceRecord = Record<string, unknown>;
export interface AskResponse {
  mode: AskMode;
  decision_state: DecisionState;
  language: "ar" | "en";
  answer: string;
  evidence_status?: "supported" | "insufficient" | null;
  key_concepts?: { term: string; explanation: string }[] | null;
  source_excerpts?: SourceRecord[] | null;
  sources?: SourceRecord[] | null;
  clarification_question?: string | null;
  limitations?: string[] | null;
  case_details?: SourceRecord | null;
}
export function isRecord(value: unknown): value is SourceRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
