"use client";
import { useState } from "react";
import { ArrowLeft, Route, BookOpen, Clock3, Check } from "lucide-react";
import { SectionHeading } from "@/components/ui/section-heading";
import { MoonlitScene } from "./moonlit-scene";
import { pathSteps } from "@/data/home";
export function LearningPath() {
  const [expanded, setExpanded] = useState(false);
  return (
    <section className="section path-section" id="learning-path">
      <div className="container">
        <SectionHeading
          title="خطوة بخطوة .. إلى وضوح أكبر"
          description="مسار واحد، بداية بسيطة. تعلم بالترتيب الذي يناسبك."
          icon={<Route size={27} />}
        />
        <div className="learning-card">
          <div className="path-illustration">
            <MoonlitScene miniature />
            <span className="path-illustration-label">رحلة الفهم</span>
          </div>
          <div className="path-content">
            <span className="level-badge">
              <span />
              المستوى المبتدئ
            </span>
            <h3>فهم نظام المواريث في الإسلام</h3>
            <p>
              من المصطلح إلى المعنى، ومن القاعدة إلى المثال.
              <br />
              رحلة واضحة لمن يبدأ من الصفر، بلا معرفة مسبقة.
            </p>
            <div className="path-meta">
              <span>
                <BookOpen size={16} />٥ محطات تعليمية
              </span>
              <span>
                <Clock3 size={16} />
                على مهل، وبوتيرتك
              </span>
            </div>
            <div className="path-details">
              <button
                type="button"
                className="path-toggle"
                aria-expanded={expanded}
                aria-controls="beginner-path-steps"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? "إخفاء المسار" : "استكشف المسار"}
                <ArrowLeft size={17} aria-hidden="true" />
              </button>
              <div
                className="path-expansion"
                data-expanded={expanded}
                aria-hidden={!expanded}
                inert={!expanded}
                id="beginner-path-steps"
              >
                <div className="path-expansion-inner">
                  <ol>
                    {pathSteps.map((step, i) => (
                      <li key={step}>
                        <span>{i + 1}</span>
                        <a href={i === 4 ? "#examples" : "#concepts"}>{step}</a>
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
            </div>
          </div>
          <div className="path-side-note">
            <span className="path-small-arch">
              <BookOpen size={32} strokeWidth={1.3} />
            </span>
            <h4>الفهم قبل الحساب</h4>
            <p>
              مفاهيم مترابطة.
              <br />
              لغة قريبة.
              <br />
              بداية مطمئنة.
            </p>
            <span className="path-check">
              <Check size={14} />
              مناسب للجميع
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
