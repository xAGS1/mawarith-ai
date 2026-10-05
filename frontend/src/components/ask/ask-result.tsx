"use client";
import { useRef } from "react";
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
} from "@/lib/ask/presentation";

function text(value: unknown) {
  return typeof value === "string" ? value : "";
}
function records(value: unknown): SourceRecord[] {
  return Array.isArray(value) ? value.filter(isRecord) : [];
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
  const sources = uniqueSources(records(result.sources)).filter(
    (source) => !displayedSources.has(sourceIdentity(source)),
  );
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
  const allSources = uniqueSources([...excerpts, ...sources]);
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
  return (
    <section
      ref={container}
      className="ask-result"
      aria-label={t({ ar: "نتيجة السؤال", en: "Question result" })}
    >
      <p className="ask-result-question">{question}</p>
      <h3>
        {t(
          educationalInsufficiency
            ? {
                ar: "تعذر تقديم شرح موثق",
                en: "Verified explanation unavailable",
              }
            : stateLabels[result.decision_state],
        )}
      </h3>
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
      {typeof result.clarification_question === "string" &&
        result.clarification_question && (
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
      {relatives.length > 0 && (
        <div>
          <h4>
            {t({
              ar: "الأقارب المذكورون في الحالة",
              en: "Relatives mentioned in the case",
            })}
          </h4>
          <ul>
            {relatives.map((relative, i) => (
              <li key={i}>
                {text(relative.relation)}: {Number(relative.count)}
              </li>
            ))}
          </ul>
        </div>
      )}
      {verified && (
        <div className="ask-distribution">
          <h4>
            {t({
              ar: "التوزيع المتحقق حسابيًا",
              en: "Arithmetically verified distribution",
            })}
          </h4>
          <div className="ask-table-scroll">
            <table>
              <thead>
                <tr>
                  <th>{t({ ar: "الوارث", en: "Heir" })}</th>
                  <th>{t({ ar: "العدد", en: "Count" })}</th>
                  <th>{t({ ar: "نصيب الفرد", en: "Share per individual" })}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    <td>{text(row.heir)}</td>
                    <td>{Number(row.count)}</td>
                    <td dir="ltr">{text(row.per_head_shares)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {allSources.length > 0 && (
        <div className="tutor-source-chips">
          {allSources.map((source, i) => (
            <span key={i}>{text(metadata(source).source_name)}</span>
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
            ar: `${educationalInsufficiency ? "عرض المصادر المتاحة" : "عرض المصادر"} (${allSources.length})`,
            en: `${educationalInsufficiency ? "View available sources" : "View sources"} (${allSources.length})`,
          })}
        >
          {excerpts.length > 0 && (
            <div className="ask-excerpts">
              <h4>
                {t({
                  ar: "مقتطفات المصادر — النص كما ورد",
                  en: "Source excerpts — exact returned text",
                })}
              </h4>
              {excerptGroups.map((group, i) => (
                <div className="ask-source" key={i}>
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
                {t({ ar: "المصادر والمراجع", en: "Sources and references" })}
              </h4>
              {sources.map((source, i) => (
                <div className="ask-source" key={i}>
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
