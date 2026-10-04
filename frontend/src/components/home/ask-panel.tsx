"use client";
import { useLocale } from "@/i18n/locale-context";
import { useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { ask, AskError } from "@/lib/ask/client";
import type { AskResponse } from "@/lib/ask/types";
import { AskResult } from "@/components/ask/ask-result";
import { exampleQuestions } from "@/data/home";
export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const { t } = useLocale();
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
    setSubmittedQuestion(trimmed);
    try {
      setResult(await ask(trimmed));
    } catch (error) {
      setError(error instanceof AskError ? error.code : "request_error");
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }
  const errorMessages = {
    empty: { ar: "اكتب سؤالًا أولًا.", en: "Please enter a question." },
    timeout: {
      ar: "استغرق الطلب وقتًا أطول من المتوقع. حاول مجددًا.",
      en: "The request timed out. Please retry.",
    },
    backend_unavailable: {
      ar: "الخدمة غير متاحة حاليًا. حاول مجددًا.",
      en: "The backend is currently unavailable. Please retry.",
    },
    request_error: {
      ar: "تعذر إكمال الطلب. حاول مجددًا.",
      en: "The request could not be completed. Please retry.",
    },
  };
  return (
    <div className="ask-area">
      <form
        className="ask-panel"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="question-field">
          <Sparkles className="ask-sparkle" size={21} aria-hidden="true" />
          <label className="sr-only" htmlFor="question">
            {t("سؤال أو حالة مواريث")}
          </label>
          <input
            id="question"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setError(null);
            }}
            placeholder={t("اسأل عن مفهوم أو اكتب حالة مواريث...")}
            disabled={pending}
            maxLength={600}
          />
          <button
            type="submit"
            className="ask-submit"
            disabled={pending}
            aria-label={t("استكشف السؤال")}
          >
            <Send size={22} aria-hidden="true" />
          </button>
        </div>
        <div className="question-chips">
          <span>{t("جرّب أن تسأل:")}</span>
          {exampleQuestions.map((q) => (
            <button
              type="button"
              key={q.ar}
              disabled={pending}
              onClick={() => {
                setQuestion(t(q));
                setError(null);
              }}
            >
              {t(q)}
            </button>
          ))}
        </div>
      </form>
      {pending && (
        <div className="ask-feedback" role="status">
          {t({ ar: "جارٍ إعداد الإجابة…", en: "Preparing your answer…" })}
        </div>
      )}
      {error && (
        <div className="ask-feedback" role="alert">
          <p>
            {t(
              errorMessages[error as keyof typeof errorMessages] ||
                errorMessages.request_error,
            )}
          </p>
          {error !== "empty" && (
            <button
              type="button"
              onClick={() => void submit(submittedQuestion)}
            >
              {t({ ar: "حاول مجددًا", en: "Retry" })}
            </button>
          )}
        </div>
      )}
      {result && <AskResult result={result} question={submittedQuestion} />}
    </div>
  );
}
