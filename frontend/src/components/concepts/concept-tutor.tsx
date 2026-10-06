"use client";
import { useEffect, useRef, useState } from "react";
import { useLocale } from "@/i18n/locale-context";
import { ask, AskError } from "@/lib/ask/client";
import { useSessionAskState } from "@/lib/ask/use-session-ask-state";
import { AskResult } from "@/components/ask/ask-result";
import { AskLoading } from "@/components/ask/result-controls";
import type { BilingualText } from "@/data/home";

export function ConceptTutor({
  concept,
  heading,
  intro,
  surface = "concept",
}: {
  concept: { slug: string; title: BilingualText; prompts: BilingualText[] };
  heading?: BilingualText;
  intro?: BilingualText;
  surface?: "concept" | "path";
}) {
  const { t } = useLocale();
  const {
    question,
    setQuestion,
    submitted,
    setSubmitted,
    result,
    setResult,
    error,
    setError,
    initialized,
    clear,
  } = useSessionAskState(`mawarith:ask:${surface}:${concept.slug}`);
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const activeRequest = useRef<AbortController | null>(null);
  useEffect(
    () => () => {
      activeRequest.current?.abort();
    },
    [],
  );
  async function submit(value = question) {
    if (!initialized || inFlight.current) return;
    const trimmed = value.trim();
    if (!trimmed) {
      setError("empty");
      return;
    }
    inFlight.current = true;
    const controller = new AbortController();
    activeRequest.current = controller;
    setPending(true);
    setError(null);
    setSubmitted(trimmed);
    try {
      const response = await ask(
        trimmed,
        { slug: concept.slug, title: concept.title.ar },
        controller.signal,
      );
      if (!controller.signal.aborted) setResult(response);
    } catch (err) {
      if (!controller.signal.aborted)
        setError(err instanceof AskError ? err.code : "request_error");
    } finally {
      inFlight.current = false;
      if (!controller.signal.aborted) setPending(false);
    }
  }
  const messages: Record<string, { ar: string; en: string }> = {
    busy: {
      ar: "MAWARITH يعالج عدة أسئلة الآن. حاول مرة أخرى بعد لحظات.",
      en: "MAWARITH is handling several questions. Please retry in a moment.",
    },
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
        {t(
          heading || {
            ar: `اسأل MAWARITH عن ${concept.title.ar}`,
            en: `Ask MAWARITH about ${concept.title.en}`,
          },
        )}
      </h2>
      {intro && <p>{t(intro)}</p>}
      <button
        type="button"
        className="ask-clear"
        disabled={!initialized || pending}
        onClick={clear}
      >
        {t({ ar: "مسح", en: "Clear" })}
      </button>
      <div className="tutor-prompts">
        {concept.prompts.map((prompt, i) => (
          <button
            key={i}
            type="button"
            disabled={!initialized || pending}
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
            disabled={!initialized || pending}
            maxLength={2000}
            placeholder={t(concept.prompts[0])}
          />
          <button
            className="primary-button"
            disabled={!initialized || pending}
            type="submit"
          >
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
