"use client";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { useLocale } from "@/i18n/locale-context";
import Image from "next/image";
import { BookOpenText, ArrowLeft } from "lucide-react";
import {
  learningPathCurriculum,
  type LearningCurriculum,
} from "@/data/learning-paths";
import { ConceptTutor } from "@/components/concepts/concept-tutor";

export function PathShell({ path }: { path: LearningCurriculum }) {
  const { t } = useLocale();
  const previous = learningPathCurriculum[path.order - 2],
    next = learningPathCurriculum[path.order];
  return (
    <>
      <Navbar homeLinks />
      <main id="main" className="learning-path-page section">
        <div className="container curriculum-container">
          <Link className="curriculum-back" href="/#learning-path">
            {t({
              ar: "العودة إلى مسارات التعلم",
              en: "Back to Learning Paths",
            })}
          </Link>
          <header className="learning-path-hero curriculum-panel">
            <div className="learning-path-hero-content">
              <div className="curriculum-progress">
                <span>
                  {t({ ar: `${path.order} من 4`, en: `${path.order} of 4` })}
                </span>
                <span className="curriculum-track">
                  <span style={{ width: `${(path.order / 4) * 100}%` }} />
                </span>
              </div>
              <BookOpenText
                className="path-page-icon"
                size={28}
                aria-hidden="true"
              />
              <h1>{t(path.title)}</h1>
              <p className="path-page-subtitle">{t(path.subtitle)}</p>
              <p>{t(path.heroDescription)}</p>
              <div className="path-page-actions">
                <a className="primary-button" href="#path-stations">
                  {t({ ar: "ابدأ هذا المسار", en: "Start this path" })}
                  <ArrowLeft size={16} aria-hidden="true" />
                </a>
                <a className="path-page-secondary" href="#path-tutor">
                  {t({ ar: "اسأل MAWARITH", en: "Ask MAWARITH" })}
                </a>
              </div>
            </div>
            <div className="learning-path-page-image">
              <Image
                src={path.image}
                alt=""
                fill
                sizes="(max-width: 760px) 100vw, 360px"
                priority
              />
            </div>
          </header>
          <section
            className="path-page-section"
            aria-labelledby="outcomes-title"
          >
            <p className="curriculum-eyebrow">
              {t({ ar: "وجهتك في هذا المسار", en: "Your goals for this path" })}
            </p>
            <h2 id="outcomes-title">
              {t({ ar: "ماذا ستتعلم؟", en: "What will you learn?" })}
            </h2>
            <ul className="path-outcomes">
              {path.outcomes.map((outcome, i) => (
                <li key={i}>
                  <span aria-hidden="true">◇</span>
                  {t(outcome)}
                </li>
              ))}
            </ul>
          </section>
          <section
            id="path-stations"
            className="path-page-section"
            aria-labelledby="stations-title"
          >
            <p className="curriculum-eyebrow">
              {t({ ar: "خطوة بخطوة", en: "Step by step" })}
            </p>
            <h2 id="stations-title">
              {t({ ar: "محطات المسار", en: "Path stations" })}
            </h2>
            <ol className="path-stations">
              {path.stations.map((station, i) => (
                <li key={i}>
                  <span className="path-station-number" aria-hidden="true">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h3>{t(station.title)}</h3>
                    <p>{t(station.description)}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>
          <section
            className="curriculum-panel path-scenario"
            aria-labelledby="scenario-title"
          >
            <p className="curriculum-eyebrow">
              {t({
                ar: "سيناريو تعليمي · دون حساب جديد",
                en: "Educational scenario · no new calculation",
              })}
            </p>
            <h2 id="scenario-title">
              {t({ ar: "مثال سريع", en: "Quick example" })}
            </h2>
            <p>{t(path.example)}</p>
          </section>
          <section
            className="path-page-section"
            aria-labelledby="related-title"
          >
            <h2 id="related-title">
              {t({ ar: "المفاهيم المرتبطة", en: "Related concepts" })}
            </h2>
            <div className="path-related-concepts">
              {path.relatedConcepts.map((concept, i) =>
                concept.slug ? (
                  <Link key={i} href={`/concepts/${concept.slug}`}>
                    {t(concept.title)}
                    <ArrowLeft size={13} aria-hidden="true" />
                  </Link>
                ) : (
                  <span key={i}>{t(concept.title)}</span>
                ),
              )}
            </div>
          </section>
          <div id="path-tutor">
            <ConceptTutor
              surface="path"
              key={path.slug}
              concept={path}
              heading={{
                ar: "اسأل MAWARITH عن هذا المسار",
                en: "Ask MAWARITH about this path",
              }}
              intro={{
                ar: "اكتب ما تحتاج إلى فهمه. يستعين الشرح بالمصادر المعتمدة، والمسار سياق مساعد لا يقيّد سؤالك.",
                en: "Ask what you want to understand. Explanations use approved sources; the path provides context without restricting your question.",
              }}
            />
          </div>
          <nav
            className="path-page-navigation"
            aria-label={t({ ar: "التنقل بين المسارات", en: "Path navigation" })}
          >
            {previous ? (
              <Link href={`/learn/paths/${previous.slug}`}>
                <small>{t({ ar: "المسار السابق", en: "Previous path" })}</small>
                <strong>{t(previous.title)}</strong>
              </Link>
            ) : (
              <span />
            )}
            <Link href="/#learning-path">
              {t({ ar: "جميع المسارات", en: "All paths" })}
            </Link>
            {next ? (
              <Link href={`/learn/paths/${next.slug}`}>
                <small>{t({ ar: "المسار التالي", en: "Next path" })}</small>
                <strong>{t(next.title)}</strong>
              </Link>
            ) : (
              <span />
            )}
          </nav>
        </div>
      </main>
      <Footer homeLinks />
    </>
  );
}
