"use client";
import { useEffect, useId, useRef, useState, type ReactNode } from "react";
import { useLocale } from "@/i18n/locale-context";

export function ResultDisclosure({
  title,
  hideTitle,
  children,
  className = "",
}: {
  title: string;
  hideTitle?: string;
  children: ReactNode;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <div className={`result-disclosure ${className}`}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(!open)}
      >
        {open ? hideTitle || title : title}
        <span aria-hidden="true">{open ? "−" : "+"}</span>
      </button>
      <div id={id} hidden={!open}>
        {children}
      </div>
    </div>
  );
}

export function AnswerPreview({
  answer,
  collapsible,
}: {
  answer: string;
  collapsible: boolean;
}) {
  const { t } = useLocale();
  const [expanded, setExpanded] = useState(false);
  const [overflow, setOverflow] = useState(false);
  const paragraph = useRef<HTMLParagraphElement>(null);
  const id = useId();
  const long = collapsible && (answer.length > 550 || overflow);
  const end = answer.lastIndexOf(" ", 550);
  const preview =
    answer.length > 550
      ? answer.slice(0, end > 450 ? end : 550).trimEnd() + "…"
      : answer;
  useEffect(() => {
    if (!collapsible || expanded || !paragraph.current) return;
    const node = paragraph.current;
    const check = () => {
      const lineHeight = parseFloat(getComputedStyle(node).lineHeight);
      // Font ink can extend beyond a single line box. Only offer expansion
      // when the five-line preview genuinely clips another line of text.
      setOverflow(
        node.clientHeight >= lineHeight * 4.5 &&
          node.scrollHeight > node.clientHeight + lineHeight / 2,
      );
    };
    const observer = new ResizeObserver(check);
    observer.observe(node);
    check();
    return () => observer.disconnect();
  }, [answer, collapsible, expanded]);
  return (
    <>
      <p
        ref={paragraph}
        id={id}
        className={collapsible && !expanded ? "answer-preview" : undefined}
      >
        {collapsible && !expanded ? preview : answer}
      </p>
      {long && (
        <button
          type="button"
          className="answer-expand"
          aria-expanded={expanded}
          aria-controls={id}
          onClick={() => setExpanded(!expanded)}
        >
          {t(
            expanded
              ? { ar: "عرض أقل", en: "Show less" }
              : { ar: "عرض المزيد", en: "Show more" },
          )}
        </button>
      )}
    </>
  );
}

export function FollowUpInput({
  onSubmit,
  pending = false,
}: {
  onSubmit: (question: string) => void;
  pending?: boolean;
}) {
  const { t } = useLocale();
  const [question, setQuestion] = useState("");
  const id = useId();
  return (
    <form
      className="answer-follow-up"
      onSubmit={(event) => {
        event.preventDefault();
        if (question.trim() && !pending) onSubmit(question.trim());
      }}
    >
      <label htmlFor={id}>
        {t({
          ar: "هل تريد أن تسأل متابعة؟",
          en: "Would you like to ask a follow-up?",
        })}
      </label>
      <div>
        <input
          id={id}
          value={question}
          disabled={pending}
          onChange={(event) => setQuestion(event.target.value)}
          maxLength={600}
          placeholder={t({
            ar: "اكتب سؤالك هنا…",
            en: "Write your question here…",
          })}
        />
        <button
          className="primary-button"
          type="submit"
          disabled={pending || !question.trim()}
        >
          {t({ ar: "اسأل MAWARITH", en: "Ask MAWARITH" })}
        </button>
      </div>
    </form>
  );
}

export function AnswerNavigation({
  container,
}: {
  container: React.RefObject<HTMLElement | null>;
}) {
  const { t } = useLocale();
  const [visible, setVisible] = useState(false);
  const [nearBottom, setNearBottom] = useState(false);
  useEffect(() => {
    const node = container.current;
    if (!node) return;
    const check = () => {
      const rect = node.getBoundingClientRect();
      setVisible(
        rect.height > innerHeight * 1.25 &&
          rect.bottom > 0 &&
          rect.top < innerHeight,
      );
      setNearBottom(rect.bottom <= innerHeight + 120);
    };
    const observer = new ResizeObserver(check);
    observer.observe(node);
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check);
    check();
    return () => {
      observer.disconnect();
      window.removeEventListener("scroll", check);
      window.removeEventListener("resize", check);
    };
  }, [container]);
  if (!visible) return null;
  const label = t(
    nearBottom
      ? { ar: "بداية الإجابة", en: "Answer start" }
      : { ar: "نهاية الإجابة", en: "Answer end" },
  );
  return (
    <button
      className="answer-navigation"
      type="button"
      aria-label={label}
      onClick={() =>
        container.current?.scrollIntoView({
          block: nearBottom ? "start" : "end",
          behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth",
        })
      }
    >
      <span aria-hidden="true">{nearBottom ? "↑" : "↓"}</span> {label}
    </button>
  );
}

export function AskLoading() {
  const { t } = useLocale();
  return (
    <span className="ask-loading">
      <span className="ask-loading-dot" aria-hidden="true" />
      {t({
        ar: "MAWARITH يبحث في المصادر الموثوقة…",
        en: "MAWARITH is searching trusted sources…",
      })}
    </span>
  );
}
