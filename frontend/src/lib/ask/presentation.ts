import { isRecord, type SourceRecord } from "./types";

/** Display only: backend citation validation still sees the original IDs. */
export function publicText(text: string): string {
  return text
    .replace(/\[E\d+(?:\s*[,;]\s*E\d+)*\]/g, "")
    .replace(/\bE\d+\b/g, "")
    .replace(/[ \t]+([.,،؛])/g, "$1")
    .trim();
}
export function metadata(source: SourceRecord): SourceRecord {
  return {
    ...(isRecord(source.provenance) ? source.provenance : {}),
    ...source,
    ...(isRecord(source.source) ? source.source : {}),
  };
}
function stable(value: unknown): string {
  if (isRecord(value))
    return JSON.stringify(
      Object.keys(value)
        .sort()
        .map((key) => [key, stable(value[key])]),
    );
  return JSON.stringify(value) ?? "";
}
export function uniqueSources(
  sources: SourceRecord[],
  excerpts = false,
): SourceRecord[] {
  const seen = new Set<string>();
  return sources.filter((source) => {
    const m = metadata(source);
    const key =
      stable([
        m.source_type,
        m.source_name,
        m.provider,
        m.reference ?? { volume: m.volume, page: m.page },
        m.source_url,
        m.input_file,
      ]) + (excerpts ? stable(source.text) : "");
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
export function distinctConcepts(
  concepts: SourceRecord[],
  answer: string,
): SourceRecord[] {
  const normalize = (text: string) =>
    publicText(text).replace(/\s+/g, " ").trim();
  const seen = new Set<string>();
  return concepts.filter((concept) => {
    const explanation = normalize(String(concept.explanation));
    if (
      !explanation ||
      normalize(answer).includes(explanation) ||
      seen.has(explanation)
    )
      return false;
    seen.add(explanation);
    return true;
  });
}
export function limitationText(text: string, language: "ar" | "en"): string {
  if (language !== "ar") return publicText(text);
  const messages: Record<string, string> = {
    "Arithmetic consistency does not establish legal completeness or correctness.":
      "الاتساق الحسابي لا يثبت اكتمال الحكم الشرعي أو صحته.",
    "No matching approved fiqh evidence is available.":
      "لا تتوفر أدلة فقهية معتمدة مطابقة للسؤال.",
    "Qwen timed out; returned a minimal source-bound concept explanation.":
      "انتهت مهلة الشرح؛ عُرض شرح موجز مرتبط بالمصادر المتاحة.",
    "Explanation timed out; no matching structured concept metadata is available for a safe fallback.":
      "انتهت مهلة الشرح، ولا تتوفر بيانات مفاهيم موثقة لإجابة بديلة آمنة.",
    "Coverage is limited to the approved local corpus; page numbers may be unavailable. Evidence-ID checks do not prove every generated claim.":
      "التغطية محدودة بالمحتوى المحلي المعتمد، وقد لا تتوفر أرقام الصفحات. التحقق من المراجع لا يثبت صحة كل عبارة مولّدة.",
  };
  if (messages[text]) return messages[text];
  if (text.startsWith("Evidence retrieval unavailable:"))
    return "تعذر استرجاع الأدلة المعتمدة.";
  if (text.startsWith("Explanation withheld:"))
    return "لم يُعرض الشرح لعدم اجتياز التحقق من الأدلة.";
  return publicText(text);
}
