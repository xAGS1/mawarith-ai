"use client";
import { useLocale } from "@/i18n/locale-context";
import Link from "next/link";
import { ArrowLeft, BookOpenText } from "lucide-react";
import { concepts } from "@/data/home";
import { ConceptIcon } from "@/components/ui/icons";
import { SectionHeading } from "@/components/ui/section-heading";
export function ConceptCards() {
  const { t } = useLocale();
  return (
    <section className="section concepts-section" id="concepts">
      <div className="container">
        <SectionHeading
          title={t("مفاهيم صغيرة، فهم أعمق")}
          description={t(
            "ابدأ من الأساسيات. كل مفهوم يفتح لك بابًا جديدًا للفهم.",
          )}
          icon={<BookOpenText size={27} />}
          href="#learning-path"
          linkText={t("ابدأ مسارك التعليمي")}
        />
        <div className="concept-grid">
          {concepts.map((concept, i) => (
            <Link
              key={concept.id}
              className="concept-card"
              href={`/concepts/${concept.id === "residuary-heirs" ? "asabah" : concept.id === "residuary-inheritance" ? "tasib" : concept.id}`}
            >
              <span className="concept-index" dir="ltr">
                0{i + 1}
              </span>
              <ConceptIcon name={concept.icon} className="concept-icon" />
              <h3>{t(concept.title)}</h3>
              <p>{t(concept.description)}</p>
              <span className="card-discover">
                {t("اكتشف المفهوم")}
                <ArrowLeft size={14} aria-hidden="true" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
