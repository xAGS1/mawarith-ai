"use client";
import { useRef } from "react";
import { ReadyResult, CaseUnderstanding } from "./ready-result";
import { DecisionResultCard } from "./decision-result-card";
import {
  ResultDisclosure,
  AnswerPreview,
  FollowUpInput,
  AnswerNavigation,
} from "./result-controls";
import { useLocale } from "@/i18n/locale-context";
import { isRecord, type AskResponse, type SourceRecord } from "@/lib/ask/types";

import {
  publicText,
  metadata,
  uniqueSources,
  distinctConcepts,
  limitationText,
  groupExcerpts,
  sourceIdentity,
  summaryReference,
  uniqueSummaryReferences,
} from "@/lib/ask/presentation";

function text(value: unknown) {
  return typeof value === "string" ? value : "";
}
function records(value: unknown): SourceRecord[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
}
function duplicatesClarification(answer: string, clarification: string) {
  const normalize = (value: string) =>
    publicText(value)
      .normalize("NFKC")
      .toLowerCase()
      .replace(/[\u064b-\u065f\u0670]/g, "")
      .replace(/[^\p{L}\p{N}\s]/gu, " ")
      .replace(/\s+/g, " ")
      .trim();
  const a = normalize(answer);
  const c = normalize(clarification);
  if (!a) return true;
  if (!c) return false;
  if (a === c) return true;
  const words = a.split(" ");
  const clarificationWords = new Set(c.split(" "));
  return (
    words.filter((word) => clarificationWords.has(word)).length /
      words.length >=
    0.8
  );
}
function SourceMetadata({ source }: { source: SourceRecord }) {
  const { t } = useLocale();
  const m = metadata(source);
  const reference = isRecord(m.reference) ? m.reference : null;
  const fields = [
    { label: t({ ar: "المصدر", en: "Source" }), value: text(m.source_name) },
    {
      label: t({ ar: "المدخل / الموضوع", en: "Entry / topic" }),
      value: text(m.section) || text(m.topic),
    },
    {
      label: t({ ar: "الناشر / المؤسسة", en: "Publisher / institution" }),
      value: text(m.publisher) || text(m.institution),
    },
    {
      label: t({ ar: "المرجع", en: "Reference" }),
      value: reference
        ? [
            reference.volume != null
              ? `${t({ ar: "الجزء", en: "Volume" })} ${reference.volume}`
              : "",
            reference.page != null
              ? `${t({ ar: "الصفحة", en: "Page" })} ${reference.page}`
              : "",
          ]
            .filter(Boolean)
            .join(" / ")
        : [
            text(m.reference),
            m.volume != null
              ? `${t({ ar: "الجزء", en: "Volume" })} ${m.volume}`
              : "",
            m.page != null
              ? `${t({ ar: "الصفحة", en: "Page" })} ${m.page}`
              : "",
          ]
            .filter(Boolean)
            .join(" / "),
    },
  ];
  const url = text(m.source_url) || text(m.canonical_url);
  return (
    <dl className="ask-source-meta">
      {fields
        .filter((field) => field.value)
        .map((field) => (
          <div key={field.label}>
            <dt>{field.label}</dt>
            <dd>{publicText(field.value)}</dd>
          </div>
        ))}
      {/^https?:\/\//i.test(url) && (
        <div>
          <dt>{t({ ar: "الرابط", en: "Link" })}</dt>
          <dd>
            <a href={url} target="_blank" rel="noopener noreferrer">
              {url}
            </a>
          </dd>
        </div>
      )}
    </dl>
  );
}

export function AskResult({
  result,
  question,
  compactSources = false,
  onFollowUp,
  pending = false,
}: {
  result: AskResponse;
  question: string;
  compactSources?: boolean;
  onFollowUp?: (question: string) => void;
  pending?: boolean;
}) {
  const { t } = useLocale();
  const container = useRef<HTMLElement>(null);
  const stateLabels = {
    ready: { ar: "الإجابة", en: "Answer" },
    needs_clarification: { ar: "يلزم توضيح", en: "Clarification needed" },
    specialist_referral: {
      ar: "إحالة إلى مختص — لا يوجد توزيع نهائي",
      en: "Specialist referral — no final distribution",
    },
    out_of_scope: { ar: "خارج نطاق الخدمة", en: "Out of scope" },
  };
  const educationalInsufficiency =
    result.mode === "learn" &&
    (result.decision_state === "specialist_referral" ||
      (result.evidence_status === "insufficient" &&
        result.decision_state !== "needs_clarification"));
  const details = isRecord(result.case_details) ? result.case_details : null;
  const parsed =
    details && isRecord(details.parsed_relations)
      ? details.parsed_relations
      : null;
  const relatives = parsed
    ? records(parsed.mentioned_relatives).filter(
        (relative) =>
          typeof relative.relation === "string" &&
          Number.isInteger(relative.count) &&
          Number(relative.count) > 0,
      )
    : [];
  const calculation =
    details && isRecord(details.result) ? details.result : null;
  const verification =
    calculation && isRecord(calculation.verification)
      ? calculation.verification
      : null;
  const post =
    calculation && isRecord(calculation.post_tasil)
      ? calculation.post_tasil
      : null;
  const rows = post ? records(post.distribution) : [];
  const verified =
    result.mode === "case" &&
    result.decision_state === "ready" &&
    verification?.is_consistent === true &&
    verification?.total_fraction === "1" &&
    rows.length > 0 &&
    rows.every(
      (row) =>
        typeof row.heir === "string" &&
        Number.isInteger(row.count) &&
        Number(row.count) > 0 &&
        typeof row.per_head_shares === "string",
    );
  const excerpts =
    result.mode === "learn" &&
    (result.decision_state !== "ready" || educationalInsufficiency)
      ? []
      : uniqueSources(
          records(result.source_excerpts).filter(
            (source) => typeof source.text === "string",
          ),
          true,
        ).slice(0, result.mode === "learn" ? 2 : undefined);
  const excerptGroups = groupExcerpts(excerpts);
  const displayedSources = new Set(excerpts.map(sourceIdentity));
  const hasRule = (source: SourceRecord) =>
    typeof source.rule === "string" || typeof source.rule_id === "string";
  const sources = [
    ...records(result.sources).filter(hasRule),
    ...uniqueSources(
      records(result.sources).filter((source) => !hasRule(source)),
    ).filter((source) => !displayedSources.has(sourceIdentity(source))),
  ];
  const concepts = distinctConcepts(
    records(result.key_concepts).filter(
      (concept) =>
        typeof concept.term === "string" &&
        typeof concept.explanation === "string",
    ),
    result.answer,
  );
  const limitations = Array.isArray(result.limitations)
    ? result.limitations.filter((item) => typeof item === "string")
    : [];
  const allSources = uniqueSummaryReferences([...excerpts, ...sources]);
  // Only known, purely operational notes may be collapsed. Unrecognized or
  // religious/safety limitations remain visible rather than being guessed safe.
  const routineNotes = new Set([
    "Page numbers may be unavailable.",
    "أرقام الصفحات قد لا تكون متاحة.",
  ]);
  const warnings = limitations.filter(
    (item) => result.decision_state !== "ready" || !routineNotes.has(item),
  );
  const notes = limitations.filter(
    (item) => result.decision_state === "ready" && routineNotes.has(item),
  );
  const hideExplanation =
    result.decision_state === "needs_clarification" &&
    duplicatesClarification(result.answer, result.clarification_question || "");
  const explanation = hideExplanation ? null : (
    <div
      className="ask-answer"
      lang={result.language}
      dir={result.language === "ar" ? "rtl" : "ltr"}
    >
      <h4>
        {t(
          result.mode === "learn"
            ? { ar: "الشرح التعليمي", en: "Educational explanation" }
            : { ar: "شرح النتيجة", en: "Result explanation" },
        )}
      </h4>
      <AnswerPreview
        key={question + result.answer}
        answer={publicText(result.answer)}
        collapsible={
          result.decision_state === "ready" && !educationalInsufficiency
        }
      />
    </div>
  );
  return (
    <section
      ref={container}
      className="ask-result"
      dir={
        result.decision_state === "needs_clarification"
          ? result.language === "ar"
            ? "rtl"
            : "ltr"
          : undefined
      }
      aria-label={t({ ar: "نتيجة السؤال", en: "Question result" })}
    >
      <p
        className="ask-result-question"
        dir={
          result.decision_state === "needs_clarification" ? "auto" : undefined
        }
      >
        {question}
      </p>
      <h3 tabIndex={-1}>
        {t(
          educationalInsufficiency
            ? {
                ar: "تعذر تقديم شرح موثق",
                en: "Verified explanation unavailable",
              }
            : stateLabels[result.decision_state],
        )}
      </h3>
      {result.decision_state === "ready" && !educationalInsufficiency ? (
        <ReadyResult
          rows={rows}
          verification={verification}
          relatives={result.mode === "case" ? relatives : []}
          verified={verified}
        >
          {explanation}
        </ReadyResult>
      ) : (
        <DecisionResultCard result={result}>
          {result.mode === "case" && (
            <CaseUnderstanding relatives={relatives} />
          )}{" "}
          {explanation}
        </DecisionResultCard>
      )}
      {(concepts.length > 0 || notes.length > 0) && (
        <ResultDisclosure
          title={t({ ar: "تفاصيل الإجابة", en: "Answer details" })}
        >
          {concepts.length > 0 && (
            <div>
              <h4>{t({ ar: "المفاهيم المرتبطة", en: "Key concepts" })}</h4>
              <dl>
                {concepts.map((concept, i) => (
                  <div key={i}>
                    <dt>{publicText(text(concept.term))}</dt>
                    <dd>{publicText(text(concept.explanation))}</dd>
                  </div>
                ))}
              </dl>
            </div>
          )}
          {notes.length > 0 && (
            <ul>
              {notes.map((item, i) => (
                <li key={i}>{limitationText(item, result.language)}</li>
              ))}
            </ul>
          )}
        </ResultDisclosure>
      )}
      {allSources.length > 0 && (
        <div className="tutor-source-chips">
          <h4>
            {t({
              ar: `المراجع المستخدمة · ${allSources.length}`,
              en: `References used · ${allSources.length}`,
            })}
          </h4>
          {allSources.map((source, i) => (
            <button
              type="button"
              key={summaryReference(source).key}
              onClick={() => {
                const button =
                  container.current?.querySelector<HTMLButtonElement>(
                    ".answer-source-disclosure > button, .tutor-source-disclosure > button",
                  );
                if (button?.getAttribute("aria-expanded") === "false")
                  button.click();
                requestAnimationFrame(() =>
                  Array.from(
                    container.current?.querySelectorAll<HTMLElement>(
                      ".ask-source",
                    ) || [],
                  )
                    .find(
                      (el) =>
                        el.dataset.referenceKey ===
                        summaryReference(source).key,
                    )
                    ?.focus({ preventScroll: true }),
                );
              }}
            >
              {summaryReference(source).name}
              {summaryReference(source).reference
                ? ` · ${summaryReference(source).reference}`
                : summaryReference(source).volume != null
                  ? ` · ${t({ ar: "الجزء", en: "Vol." })} ${summaryReference(source).volume}`
                  : summaryReference(source).page != null
                    ? ` · ${t({ ar: "الصفحة", en: "Page" })} ${summaryReference(source).page}`
                    : ""}
            </button>
          ))}
        </div>
      )}
      {allSources.length > 0 && (
        <ResultDisclosure
          className={
            compactSources
              ? "tutor-source-disclosure"
              : "answer-source-disclosure"
          }
          title={t({
            ar: "عرض التفاصيل",
            en: "View details",
          })}
        >
          {excerpts.length > 0 && (
            <div className="ask-excerpts">
              <h4>
                {t({
                  ar: "مقتطفات المصادر",
                  en: "Source excerpts",
                })}
              </h4>
              {excerptGroups.map((group, i) => (
                <div
                  className="ask-source"
                  data-reference-key={summaryReference(group.source).key}
                  tabIndex={-1}
                  key={i}
                >
                  <SourceMetadata source={group.source} />
                  <ResultDisclosure
                    title={t({
                      ar: "عرض النص من المصدر",
                      en: "Show source text",
                    })}
                    hideTitle={t({ ar: "إخفاء النص", en: "Hide text" })}
                    className="source-text-disclosure"
                  >
                    <div
                      className="source-excerpt-scroll"
                      tabIndex={0}
                      role="region"
                      aria-label={t({
                        ar: "النص الأصلي من المصدر",
                        en: "Exact source text",
                      })}
                    >
                      {group.excerpts.map((source, j) => (
                        <figure key={j}>
                          <blockquote dir="auto">
                            {text(source.text)}
                          </blockquote>
                        </figure>
                      ))}
                    </div>
                  </ResultDisclosure>
                </div>
              ))}
            </div>
          )}
          {sources.length > 0 && (
            <div>
              <h4>
                {t({
                  ar: "القواعد المطبقة ومراجعها",
                  en: "Applied rules and references",
                })}
              </h4>
              {sources.map((source, i) => (
                <div
                  className="ask-source"
                  data-reference-key={summaryReference(source).key}
                  tabIndex={-1}
                  key={i}
                >
                  <SourceMetadata source={source} />
                  {typeof source.rule === "string" && (
                    <ResultDisclosure
                      title={t({
                        ar: "عرض ملخص القاعدة",
                        en: "Show rule summary",
                      })}
                    >
                      <p>{publicText(source.rule)}</p>
                    </ResultDisclosure>
                  )}
                </div>
              ))}
            </div>
          )}
        </ResultDisclosure>
      )}
      {warnings.length > 0 && (
        <div className="answer-safety-notes">
          <h4>{result.language === "ar" ? "حدود الإجابة" : "Limitations"}</h4>
          <ul>
            {warnings.map((item, i) => (
              <li key={i}>{limitationText(item, result.language)}</li>
            ))}
          </ul>
        </div>
      )}
      <AnswerNavigation container={container} />
      {onFollowUp && <FollowUpInput onSubmit={onFollowUp} pending={pending} />}
    </section>
  );
}
