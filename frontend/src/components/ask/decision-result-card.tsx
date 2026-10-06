"use client";
import type { ReactNode } from "react";
import { useLocale } from "@/i18n/locale-context";
import type { AskResponse } from "@/lib/ask/types";
import { publicText } from "@/lib/ask/presentation";
export function DecisionResultCard({
  result,
  children,
}: {
  result: AskResponse;
  children: ReactNode;
}) {
  const { t } = useLocale();
  return (
    <div className="decision-result-card" data-decision={result.decision_state}>
      {result.clarification_question && (
        <div className="ask-clarification">
          <h4>{t({ ar: "سؤال التوضيح", en: "Clarification question" })}</h4>
          <p>{publicText(result.clarification_question)}</p>
          <small>
            {t({
              ar: "عدّل سؤالك أعلاه وأرسله مجددًا.",
              en: "Edit your question above and submit it again.",
            })}
          </small>
        </div>
      )}
      {result.mode === "case" &&
        result.decision_state === "specialist_referral" && (
          <p className="decision-next-step">
            {t({
              ar: "توقف النظام حفاظًا على سلامة النتيجة. راجع حدود الإجابة واستعن بمختص قبل اعتماد أي توزيع.",
              en: "The system stopped to protect the result. Review the limitations and consult a specialist before relying on any distribution.",
            })}
          </p>
        )}
      {children}
    </div>
  );
}
