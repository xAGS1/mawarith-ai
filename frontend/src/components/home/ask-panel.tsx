"use client";
import { useLocale } from "@/i18n/locale-context";
import { useState } from "react";
import { ArrowLeft, Send, Sparkles } from "lucide-react";
import { exampleQuestions } from "@/data/home";
export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const { t } = useLocale();
  return (
    <div className="ask-area">
      <form
        className="ask-panel"
        onSubmit={(e) => {
          e.preventDefault();
          if (question.trim()) setSubmitted(true);
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
              setSubmitted(false);
            }}
            placeholder={t("اسأل عن مفهوم أو اكتب حالة مواريث...")}
            required
            maxLength={600}
          />
          <button
            type="submit"
            className="ask-submit"
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
              onClick={() => {
                setQuestion(t(q));
                setSubmitted(false);
              }}
            >
              {t(q)}
            </button>
          ))}
        </div>
      </form>
      {submitted && (
        <div className="question-preview" role="status">
          <strong>
            {t("سؤالك:")} {question}
          </strong>
          <p>{t("استكشف المفاهيم والأمثلة التعليمية في هذه المعاينة.")}</p>
          <a href="#concepts">
            {t("متابعة الاستكشاف")}
            <ArrowLeft size={15} />
          </a>
        </div>
      )}
    </div>
  );
}
