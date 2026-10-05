"use client";
import { useRef, useState } from "react";
import { useLocale } from "@/i18n/locale-context";
import { ask, AskError } from "@/lib/ask/client";
import type { AskResponse } from "@/lib/ask/types";
import { AskResult } from "@/components/ask/ask-result";
import { AskLoading } from "@/components/ask/result-controls";
import type { CurriculumConcept } from "@/data/concept-curriculum";

export function ConceptTutor({ concept }: { concept: CurriculumConcept }) {
  const { t } = useLocale();
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState("");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inFlight = useRef(false);
  async function submit(value = question) {
    if (inFlight.current) return;
    const trimmed = value.trim();
    if (!trimmed) {
      setError("empty");
      return;
    }
    inFlight.current = true;
    setPending(true);
    setError(null);
    setResult(null);
    setSubmitted(trimmed);
    try {
      setResult(
        await ask(trimmed, { slug: concept.slug, title: concept.title.ar }),
      );
    } catch (err) {
      setError(err instanceof AskError ? err.code : "request_error");
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }
  const messages: Record<string, { ar: string; en: string }> = {
    empty: { ar: "اكتب سؤالًا أولًا.", en: "Please enter a question." },
    timeout: {
      ar: "استغرق الطلب وقتًا أطول من المتوقع. حاول مجددًا.",
      en: "The request timed out. Please retry.",
    },
    backend_unavailable: {
      ar: "الخدمة غير متاحة حاليًا. يمكنك متابعة القراءة أو المحاولة مجددًا.",
      en: "The service is unavailable. You can keep reading or retry.",
    },
    request_error: {
      ar: "تعذر إكمال الطلب. حاول مجددًا.",
      en: "The request could not be completed. Please retry.",
    },
  };
  return (
    <section
      className="concept-tutor curriculum-panel"
      aria-labelledby="tutor-title"
    >
      <p className="curriculum-eyebrow">
        {t({ ar: "هل تريد أن تسأل أكثر؟", en: "Want to ask more?" })}
      </p>
      <h2 id="tutor-title">
        {t({
          ar: `اسأل MAWARITH عن ${concept.title.ar}`,
          en: `Ask MAWARITH about ${concept.title.en}`,
        })}
      </h2>
      <div className="tutor-prompts">
        {concept.prompts.map((prompt, i) => (
          <button
            key={i}
            type="button"
            disabled={pending}
            onClick={() => setQuestion(t(prompt))}
          >
            {t(prompt)}
          </button>
        ))}
      </div>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
        aria-busy={pending}
      >
        <label htmlFor="concept-question">
          {t({ ar: "سؤالك", en: "Your question" })}
        </label>
        <div className="tutor-input-row">
          <input
            id="concept-question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            disabled={pending}
            maxLength={2000}
            placeholder={t(concept.prompts[0])}
          />
          <button className="primary-button" disabled={pending} type="submit">
            {t(
              pending
                ? { ar: "جارٍ البحث والشرح…", en: "Searching and explaining…" }
                : { ar: "اسأل MAWARITH", en: "Ask MAWARITH" },
            )}
          </button>
        </div>
      </form>
      <div role="status" aria-live="polite">
        {pending && <AskLoading />}
      </div>
      {error && (
        <div className="ask-error" role="alert">
          <p>{t(messages[error])}</p>
          {error !== "empty" && (
            <button type="button" onClick={() => void submit(submitted)}>
              {t({ ar: "إعادة المحاولة", en: "Retry" })}
            </button>
          )}
        </div>
      )}
      {result && (
        <AskResult
          key={submitted + result.answer}
          result={result}
          question={submitted}
          compactSources
          pending={pending}
          onFollowUp={(value) => {
            setQuestion(value);
            void submit(value);
          }}
        />
      )}
    </section>
  );
}
