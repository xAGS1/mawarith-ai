"use client";
import { useState } from "react";
import { ArrowLeft, BookOpen, Scale, Sparkles } from "lucide-react";
import { exampleQuestions } from "@/data/home";
export function AskPanel() {
  const [mode, setMode] = useState<"learn" | "case">("learn");
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState(false);
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
            {mode === "learn" ? "سؤالك عن المواريث" : "مسألة المواريث"}
          </label>
          <input
            id="question"
            value={question}
            onChange={(e) => {
              setQuestion(e.target.value);
              setSubmitted(false);
            }}
            placeholder={
              mode === "learn"
                ? "ماذا تود أن تتعلم عن المواريث؟"
                : "اكتب مسألة أو اختر مثالًا بسيطًا..."
            }
            required
            maxLength={600}
          />
          <button
            type="submit"
            className="ask-submit"
            aria-label="استكشف السؤال"
          >
            <ArrowLeft size={22} aria-hidden="true" />
          </button>
        </div>
        <div className="question-chips">
          <span>جرّب أن تسأل:</span>
          {exampleQuestions.map((q) => (
            <button
              type="button"
              key={q}
              onClick={() => {
                setQuestion(q);
                setMode("learn");
                setSubmitted(false);
              }}
            >
              {q}
            </button>
          ))}
        </div>
      </form>
      <div className="mode-selector" role="group" aria-label="اختيار الوضع">
        <button
          aria-pressed={mode === "learn"}
          className={mode === "learn" ? "selected" : ""}
          onClick={() => {
            setMode("learn");
            setSubmitted(false);
          }}
        >
          <BookOpen size={18} aria-hidden="true" />
          وضع التعلم<span>افهم المفاهيم</span>
        </button>
        <button
          aria-pressed={mode === "case"}
          className={mode === "case" ? "selected" : ""}
          onClick={() => {
            setMode("case");
            setSubmitted(false);
          }}
        >
          <Scale size={18} aria-hidden="true" />
          وضع المسائل<span>استكشف الأمثلة</span>
        </button>
      </div>
      {submitted && (
        <div className="question-preview" role="status">
          <strong>سؤالك: {question}</strong>
          <p>
            رحلتك تبدأ بالفهم. استكشف{" "}
            {mode === "learn" ? "بطاقات المفاهيم" : "الأمثلة التعليمية"} في هذه
            المعاينة.
          </p>
          <a href={mode === "learn" ? "#concepts" : "#examples"}>
            متابعة الاستكشاف <ArrowLeft size={15} />
          </a>
        </div>
      )}
    </div>
  );
}
