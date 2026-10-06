"use client";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { useLocale } from "@/i18n/locale-context";
import {
  calculationPaths,
  type CalculationPath,
} from "@/data/calculation-paths";
import { curriculum } from "@/data/concept-curriculum";

export function CalculationLesson({ path }: { path: CalculationPath }) {
  const { t } = useLocale();
  const previous = calculationPaths[path.order - 2],
    next = calculationPaths[path.order];
  return (
    <>
      <Navbar homeLinks />
      <main className="section calculation-lesson" id="main">
        <div className="container curriculum-container">
          <Link className="curriculum-back" href="/#examples">
            {t({ ar: "جميع مسارات الحساب", en: "All calculation paths" })}
          </Link>
          <header className="curriculum-panel calculation-lesson-hero">
            <div className="curriculum-progress">
              <span>{t({ ar: "مسار حساب", en: "Calculation path" })}</span>
              <span>
                {t({ ar: `${path.order} من 4`, en: `${path.order} of 4` })}
              </span>
            </div>
            <h1>{t(path.title)}</h1>
            <p>{t(path.intro)}</p>
          </header>
          <section className="path-page-section" aria-labelledby="method-title">
            <h2 id="method-title">
              {t({ ar: "كيف تعمل؟", en: "How does it work?" })}
            </h2>
            <ol className="calculation-steps">
              {path.steps.map((step, i) => (
                <li key={i}>
                  <span aria-hidden="true">0{i + 1}</span>
                  <p>{t(step)}</p>
                </li>
              ))}
            </ol>
          </section>
          <section
            className="curriculum-panel calculation-lesson-example"
            aria-labelledby="example-title"
          >
            <p className="curriculum-eyebrow">
              {t(
                path.conceptual
                  ? {
                      ar: "مثال مفاهيمي · دون كسور مصطنعة",
                      en: "Conceptual example · no invented fractions",
                    }
                  : { ar: "مثال تطبيقي", en: "Applied example" },
              )}
            </p>
            <h2 id="example-title">{t({ ar: "مثال", en: "Example" })}</h2>
            <p className="calculation-case">{t(path.example)}</p>
            <h3>
              {t({
                ar: "كيف وصلنا للنتيجة؟",
                en: "How do we reach the result?",
              })}
            </h3>
            <ol className="calculation-explanation">
              {path.explanation.map((step, i) => (
                <li key={i}>{t(step)}</li>
              ))}
            </ol>
            <div className="calculation-evidence">
              <p className="curriculum-eyebrow">
                {t({ ar: "مصادر هذا الدرس", en: "Lesson sources" })}
              </p>
              {path.sources.map((source) => (
                <details key={source.chunk_id}>
                  <summary>
                    {source.source_name} ·{" "}
                    {source.page
                      ? t({
                          ar: `صفحة ${source.page}`,
                          en: `Page ${source.page}`,
                        })
                      : source.section}
                  </summary>
                  <p>
                    {source.institution || source.publisher}
                    {source.volume
                      ? ` · ${t({ ar: "المجلد", en: "Volume" })} ${source.volume}`
                      : ""}
                  </p>
                  <p>{source.topic || source.section}</p>
                  <blockquote dir="rtl" lang="ar">
                    {source.text}
                  </blockquote>
                  {(source.canonical_url || source.source_url) && (
                    <a
                      href={source.canonical_url || source.source_url || ""}
                      target="_blank"
                      rel="noreferrer"
                    >
                      {t({ ar: "المصدر الأصلي", en: "Original source" })}
                    </a>
                  )}
                </details>
              ))}
              {path.ruleSummaries.map((rule) => (
                <details key={rule.rule_id}>
                  <summary>
                    {rule.topic} · {rule.source.source_name}{" "}
                    {rule.source.reference}
                  </summary>
                  <p>
                    {t({
                      ar: "ملخص قاعدة منظمة من المستودع، وليس اقتباسًا من القرآن.",
                      en: "Repository structured rule summary, not a Quran quotation.",
                    })}
                  </p>
                  <p lang="ar" dir="rtl">
                    {rule.rule}
                  </p>
                </details>
              ))}
            </div>
          </section>
          <section
            className="path-page-section calculation-try"
            aria-labelledby="try-title"
          >
            <h2 id="try-title">
              {t({ ar: "جرّب بنفسك", en: "Try it yourself" })}
            </h2>
            <p>{t(path.tryCase)}</p>
            <p className="curriculum-note">
              {t({
                ar: "راجع الحالة ثم أرسلها بنفسك. يحدد النظام ما إذا كان الحساب مدعومًا، أو يحتاج استيضاحًا أو إحالة؛ المثال التعليمي لا يضمن دعم الحساب.",
                en: "Review and submit the case yourself. The system determines whether calculation is supported, needs clarification, or requires referral; the educational example does not guarantee calculation support.",
              })}
            </p>
            <Link
              className="primary-button"
              href={`/?case=${encodeURIComponent(t(path.tryCase))}#main`}
            >
              {t({ ar: "جرّب هذه الحالة", en: "Try this case" })}
            </Link>
          </section>
          <section className="path-page-section">
            <h2>{t({ ar: "المفاهيم المرتبطة", en: "Related concepts" })}</h2>
            <div className="path-related-concepts">
              {path.relatedConcepts.map((slug) => (
                <Link key={slug} href={`/concepts/${slug}`}>
                  {t(
                    curriculum.find((concept) => concept.slug === slug)!.title,
                  )}
                </Link>
              ))}
            </div>
          </section>
          <nav
            className="path-page-navigation"
            aria-label={t({
              ar: "التنقل بين مسارات الحساب",
              en: "Calculation path navigation",
            })}
          >
            {previous ? (
              <Link href={`/learn/calculation/${previous.slug}`}>
                <small>{t({ ar: "السابق", en: "Previous" })}</small>
                {t(previous.title)}
              </Link>
            ) : (
              <span />
            )}
            <Link href="/#examples">
              {t({ ar: "جميع المسارات", en: "All paths" })}
            </Link>
            {next ? (
              <Link href={`/learn/calculation/${next.slug}`}>
                <small>{t({ ar: "التالي", en: "Next" })}</small>
                {t(next.title)}
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
