"use client";
import { useLocale } from "@/i18n/locale-context";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Send, FileText, Lightbulb } from "lucide-react";
import { ask, AskError } from "@/lib/ask/client";
import { AskResult } from "@/components/ask/ask-result";
import { AskLoading } from "@/components/ask/result-controls";
import { exampleQuestions } from "@/data/home";
import { useSessionAskState } from "@/lib/ask/use-session-ask-state";
export function AskPanel({
  workspace,
  onActiveChange,
}: {
  workspace: HTMLElement | null;
  onActiveChange: (active: boolean) => void;
}) {
  const {
    question,
    setQuestion,
    submitted: submittedQuestion,
    setSubmitted: setSubmittedQuestion,
    result,
    setResult,
    error,
    setError,
    initialized,
    clear,
  } = useSessionAskState("mawarith:ask:home");
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const activeRequest = useRef<AbortController | null>(null);
  const { t } = useLocale();
  const [cancelled, setCancelled] = useState(false);
  const textarea = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    onActiveChange(Boolean(pending || submittedQuestion || result || error));
  }, [pending, submittedQuestion, result, error, onActiveChange]);
  useEffect(() => {
    const node = textarea.current;
    if (!node) return;
    node.style.height = "auto";
    const line = parseFloat(getComputedStyle(node).lineHeight);
    node.style.height = `${Math.min(node.scrollHeight, line * 4 + 18)}px`;
  }, [question]);
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const preset = params.get("case");
    if (preset && preset.length <= 600 && !inFlight.current) {
      setQuestion(preset);
      setError(null);
      params.delete("case");
      const query = params.toString();
      window.history.replaceState(
        window.history.state,
        "",
        `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`,
      );
      requestAnimationFrame(() => {
        const input = document.getElementById("question");
        input?.focus({ preventScroll: true });
        input?.scrollIntoView({ block: "center", behavior: "instant" });
      });
    }
  }, []);
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
    setCancelled(false);
    setError(null);
    setSubmittedQuestion(trimmed);
    try {
      const response = await ask(trimmed, undefined, controller.signal);
      if (!controller.signal.aborted) {
        setResult(response);
        requestAnimationFrame(() => {
          if (
            !document.activeElement?.matches("textarea:not(#question), input")
          )
            workspace
              ?.querySelector<HTMLElement>(".ask-result > h3")
              ?.focus({ preventScroll: true });
        });
      }
    } catch (error) {
      if (!controller.signal.aborted)
        setError(error instanceof AskError ? error.code : "request_error");
    } finally {
      if (activeRequest.current === controller) {
        inFlight.current = false;
        if (!controller.signal.aborted) setPending(false);
      }
    }
  }
  const errorMessages = {
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
        aria-busy={pending}
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <div className="question-field">
          <label className="sr-only" htmlFor="question">
            {t("سؤال أو حالة مواريث")}
          </label>
          <textarea
            ref={textarea}
            rows={2}
            onKeyDown={(event) => {
              if (
                event.key === "Enter" &&
                !event.shiftKey &&
                !event.nativeEvent.isComposing
              ) {
                event.preventDefault();
                void submit();
              }
            }}
            id="question"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setError(null);
            }}
            placeholder={t({
              ar: "اكتب سؤالك عن المواريث هنا...",
              en: "Write your inheritance question here...",
            })}
            disabled={!initialized || pending}
            maxLength={600}
          />
        </div>
        <div className="composer-actions">
          <button
            type="button"
            className="composer-examples"
            onClick={() =>
              document
                .querySelector<HTMLButtonElement>(".question-chips button")
                ?.focus()
            }
            disabled={pending}
          >
            <Lightbulb size={18} aria-hidden="true" />
            {t({ ar: "أمثلة للأسئلة", en: "Example questions" })}
          </button>
          <div className="composer-tools">
            <button
              type="submit"
              className="ask-submit"
              disabled={!initialized || pending}
              aria-label={t("استكشف السؤال")}
            >
              <Send size={22} aria-hidden="true" />
            </button>
            <button
              type="button"
              className="ask-clear"
              disabled={!initialized || pending}
              onClick={() => {
                clear();
                setCancelled(false);
              }}
            >
              {t({ ar: "مسح", en: "Clear" })}
            </button>
            {pending && (
              <button
                type="button"
                className="ask-cancel"
                onClick={() => {
                  activeRequest.current?.abort();
                  activeRequest.current = null;
                  inFlight.current = false;
                  setPending(false);
                  setCancelled(true);
                }}
              >
                {t({ ar: "إلغاء الطلب", en: "Cancel request" })}
              </button>
            )}
          </div>
        </div>
      </form>
      <div className="hero-examples-collapse">
        <div>
          <div className="question-chips">
            <span>{t("جرّب أن تسأل:")}</span>
            {exampleQuestions.map((q) => (
              <button
                type="button"
                key={q.ar}
                disabled={!initialized || pending}
                onClick={() => {
                  setQuestion(t(q));
                  void submit(t(q));
                }}
              >
                <FileText size={16} aria-hidden="true" />
                {t(q)}
              </button>
            ))}
          </div>
        </div>
      </div>
      {workspace &&
        createPortal(
          <>
            {cancelled && (
              <p role="status" className="ask-feedback">
                {t({
                  ar: "تم إلغاء الطلب. يمكنك تعديل سؤالك وإرساله مجددًا.",
                  en: "Request cancelled. You can edit your question and send it again.",
                })}
              </p>
            )}
            {pending && (
              <div className="ask-feedback" role="status">
                <AskLoading />
                <div className="answer-skeleton" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                </div>
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
            {!pending && result && (
              <AskResult
                key={submittedQuestion + result.answer}
                result={result}
                question={submittedQuestion}
                pending={pending}
              />
            )}
          </>,
          workspace,
        )}
    </div>
  );
}
