"use client";
import { useLocale } from "@/i18n/locale-context";
import { useEffect, useRef, useState } from "react";
import { Send, Sparkles } from "lucide-react";
import { ask, AskError } from "@/lib/ask/client";
import type { AskResponse } from "@/lib/ask/types";
import { AskResult } from "@/components/ask/ask-result";
import { exampleQuestions } from "@/data/home";
import {
  readPendingRequest,
  markPendingRequest,
  clearPendingRequest,
  PENDING_MAX_AGE,
} from "@/lib/ask/pending-request";
export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const leavingPage = useRef(false);
  const [initialized, setInitialized] = useState(false);
  const [restoredPending, setRestoredPending] = useState(false);
  const [expired, setExpired] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const { t } = useLocale();
  useEffect(() => {
    const onLeave = () => {
      leavingPage.current = true;
    };
    const onReturn = () => {
      leavingPage.current = false;
    };
    window.addEventListener("beforeunload", onLeave);
    window.addEventListener("pagehide", onLeave);
    window.addEventListener("pageshow", onReturn);
    const marker = readPendingRequest();
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (marker) {
      setQuestion(marker.question);
      setSubmittedQuestion(marker.question);
      const remaining = PENDING_MAX_AGE - (Date.now() - marker.startedAt);
      const recover = () => {
        clearPendingRequest(marker);
        inFlight.current = false;
        setPending(false);
        setRestoredPending(false);
        setExpired(true);
      };
      if (remaining <= 0) recover();
      else {
        inFlight.current = true;
        setPending(true);
        setRestoredPending(true);
        timer = setTimeout(recover, remaining);
      }
    }
    setInitialized(true);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("beforeunload", onLeave);
      window.removeEventListener("pagehide", onLeave);
      window.removeEventListener("pageshow", onReturn);
    };
  }, []);
  async function submit(value = question) {
    if (!initialized || inFlight.current) return;
    const trimmed = value.trim();
    if (!trimmed) {
      setError("empty");
      return;
    }
    inFlight.current = true;
    const marker = markPendingRequest(trimmed);
    setExpired(false);
    setPending(true);
    setError(null);
    setResult(null);
    setSubmittedQuestion(trimmed);
    try {
      setResult(await ask(trimmed));
    } catch (error) {
      setError(error instanceof AskError ? error.code : "request_error");
    } finally {
      // Navigation can abort the browser fetch while backend generation continues.
      if (!leavingPage.current) clearPendingRequest(marker);
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
            disabled={!initialized || pending}
            maxLength={600}
          />
          <button
            type="submit"
            className="ask-submit"
            disabled={!initialized || pending}
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
              disabled={!initialized || pending}
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
          {restoredPending ? (
            <>
              <p>
                {t({
                  ar: "طلبك ما زال تحت المعالجة",
                  en: "Your request is still being processed",
                })}
              </p>
              <p>
                {t({
                  ar: "يرجى الانتظار قبل إرسال سؤال جديد.",
                  en: "Please wait before submitting another question.",
                })}
              </p>
            </>
          ) : (
            t({ ar: "جارٍ إعداد الإجابة…", en: "Preparing your answer…" })
          )}
        </div>
      )}
      {expired && (
        <div className="ask-feedback" role="status">
          <p>
            {t({
              ar: "قد تكون مهلة الطلب السابق قد انتهت. يمكنك إعادة المحاولة.",
              en: "The previous request may have expired. You can try again.",
            })}
          </p>
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
