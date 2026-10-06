"use client";
import Link from "next/link";
import { ArrowLeft, Scale } from "lucide-react";
import { useLocale } from "@/i18n/locale-context";
import { calculationPaths } from "@/data/calculation-paths";
import { SectionHeading } from "@/components/ui/section-heading";
export function InteractiveExamples() {
  const { t } = useLocale();
  return (
    <section
      className="section examples-section calculation-paths-section"
      id="examples"
    >
      <div className="container">
        <SectionHeading
          title={t({
            ar: "كيف تُبنى مسألة الميراث؟",
            en: "How is an inheritance calculation built?",
          })}
          description={t({
            ar: "تعرّف على المسارات الأساسية التي تمر بها المسألة، ثم شاهد مثالًا وجرّبه بنفسك.",
            en: "Explore the core calculation paths, see an example, and try it yourself.",
          })}
          icon={<Scale size={27} aria-hidden="true" />}
        />
        <div className="calculation-path-grid">
          {calculationPaths.map((path) => (
            <Link
              className="example-card calculation-path-card"
              key={path.slug}
              href={`/learn/calculation/${path.slug}`}
            >
              <span className="calculation-path-number" dir="ltr">
                0{path.order}
              </span>
              <h3>{t(path.title)}</h3>
              <p>{t(path.description)}</p>
              <span className="calculation-path-cta">
                {t(path.cta)}
                <ArrowLeft size={15} aria-hidden="true" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
