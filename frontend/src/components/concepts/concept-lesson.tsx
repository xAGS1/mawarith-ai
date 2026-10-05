"use client";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { ConceptIcon } from "@/components/ui/icons";
import { useLocale } from "@/i18n/locale-context";
import {
  curriculum,
  conceptEvidence,
  awlExample,
  type CurriculumConcept,
  type CurriculumEvidence,
} from "@/data/concept-curriculum";
import { ConceptTutor } from "./concept-tutor";

function EvidenceCard({ source }: { source: CurriculumEvidence }) {
  const { t } = useLocale();
  const url = source.source_url || source.canonical_url;
  return (
    <div className="curriculum-source">
      <strong>{source.source_name}</strong>
      <p>{source.institution || source.publisher}</p>
      <p>
        {source.source_id === "uqu_mawarith_1"
          ? t({
              ar: "مقرر المواريث 1 · تعريف المصطلح",
              en: "Mawarith 1 course · terminology",
            })
          : source.section || source.topic}
        {source.page &&
          ` · ${t({ ar: "صفحة PDF", en: "PDF page" })} ${source.page}`}
        {source.volume &&
          ` · ${t({ ar: "الجزء", en: "Volume" })} ${source.volume}`}
      </p>
      {url && (
        <a href={url} target="_blank" rel="noopener noreferrer">
          {t({ ar: "زيارة المصدر", en: "Visit source" })} ↗
        </a>
      )}
      <details>
        <summary>
          {t({ ar: "عرض النص من المصدر", en: "Show exact source text" })}
        </summary>
        <blockquote lang="ar" dir="rtl">
          {source.text}
        </blockquote>
      </details>
    </div>
  );
}

export function ConceptLesson({ concept }: { concept: CurriculumConcept }) {
  const { t } = useLocale();
  const index = curriculum.findIndex((item) => item.slug === concept.slug);
  const previous = curriculum[index - 1],
    next = curriculum[index + 1];
  return (
    <>
      <Navbar homeLinks />
      <main id="main" className="concept-lesson section">
        <div className="container curriculum-container">
          <Link className="curriculum-back" href="/#concepts">
            {t({ ar: "العودة إلى جميع المفاهيم", en: "Back to all concepts" })}
          </Link>
          <header className="curriculum-header">
            <div
              className="curriculum-progress"
              aria-label={t({
                ar: "التقدم في المفاهيم",
                en: "Curriculum position",
              })}
            >
              <span>
                {t({ ar: `${index + 1} من 7`, en: `${index + 1} of 7` })}
              </span>
              <span className="curriculum-track">
                <span style={{ width: `${((index + 1) / 7) * 100}%` }} />
              </span>
            </div>
            <ConceptIcon name={concept.icon} className="concept-icon" />
            <p className="curriculum-eyebrow">
              {t({
                ar: "مفهوم صغير · فهم أعمق",
                en: "One concept · deeper understanding",
              })}
            </p>
            <h1>{t(concept.title)}</h1>
            <p className="curriculum-intro">
              {t({
                ar: "اقرأ الأساس، تأمل الفكرة، ثم اسأل حين تحتاج إلى توضيح.",
                en: "Read the foundation, explore the idea, then ask when you need clarification.",
              })}
            </p>
          </header>
          <div className="curriculum-body">
            <article className="curriculum-panel">
              <p className="curriculum-eyebrow">
                {t(
                  concept.supported
                    ? {
                        ar: "ملخص تعليمي مستند إلى المصدر",
                        en: "Source-based educational summary",
                      }
                    : {
                        ar: "حدود المحتوى المتاح",
                        en: "Available content limits",
                      },
                )}
              </p>
              <h2>{t({ ar: "ما المقصود؟", en: "What does it mean?" })}</h2>
              <p className="curriculum-definition">{t(concept.definition)}</p>
              <h2>
                {t({ ar: "كيف نفهمه؟", en: "How can we understand it?" })}
              </h2>
              {concept.understanding.map((paragraph, i) => (
                <p key={i}>{t(paragraph)}</p>
              ))}
              {concept.visual.length > 0 && (
                <ol
                  className="concept-visual"
                  aria-label={t({ ar: "الفكرة الأساسية", en: "Key idea" })}
                >
                  {concept.visual.map((step, i) => (
                    <li key={i}>
                      <span>{t(step)}</span>
                    </li>
                  ))}
                </ol>
              )}
              {concept.slug === "awl" && (
                <section
                  className="curriculum-example"
                  aria-labelledby="example-title"
                >
                  <p className="curriculum-eyebrow">
                    {t({
                      ar: "مثال من المصدر · دون حساب جديد",
                      en: "Sourced example · no new calculation",
                    })}
                  </p>
                  <h2 id="example-title">{t({ ar: "مثال", en: "Example" })}</h2>
                  <h3>{t(awlExample.scenario)}</h3>
                  <p>{t(awlExample.explanation)}</p>
                  <div className="awl-origin" dir="ltr">
                    24 <span aria-hidden="true">→</span> 27
                  </div>
                  <EvidenceCard source={conceptEvidence["awl-example"]} />
                </section>
              )}
            </article>
            <aside
              className="curriculum-panel curriculum-provenance"
              aria-labelledby="source-title"
            >
              <h2 id="source-title">{t({ ar: "المصدر", en: "Source" })}</h2>
              <EvidenceCard source={conceptEvidence[concept.slug]} />
              <p className="curriculum-note">
                {t({
                  ar: "الملخص التعليمي أعلاه منفصل عن النص الأصلي. هذه الصفحة للتعلم، وليست حكمًا لحالة شخصية.",
                  en: "The educational summary is separate from the original text. This page is for learning, not a ruling on an individual case.",
                })}
              </p>
            </aside>
          </div>
          <ConceptTutor key={concept.slug} concept={concept} />
          <nav
            className="curriculum-navigation"
            aria-label={t({
              ar: "التنقل بين المفاهيم",
              en: "Concept navigation",
            })}
          >
            {previous ? (
              <Link href={`/concepts/${previous.slug}`}>
                <small>
                  {t({ ar: "المفهوم السابق", en: "Previous concept" })}
                </small>
                <strong>{t(previous.title)}</strong>
              </Link>
            ) : (
              <span />
            )}
            {next ? (
              <Link href={`/concepts/${next.slug}`}>
                <small>{t({ ar: "المفهوم التالي", en: "Next concept" })}</small>
                <strong>{t(next.title)}</strong>
              </Link>
            ) : (
              <Link href="/#concepts">
                {t({
                  ar: "العودة إلى جميع المفاهيم",
                  en: "Back to all concepts",
                })}
              </Link>
            )}
          </nav>
        </div>
      </main>
      <Footer homeLinks />
    </>
  );
}
