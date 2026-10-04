"use client";
import { useLocale } from "@/i18n/locale-context";
import { useState } from "react";
import { ArrowLeft, Lightbulb, Scale } from "lucide-react";
import { examples } from "@/data/home";
import { ConceptIcon } from "@/components/ui/icons";
import { SectionHeading } from "@/components/ui/section-heading";
import { PreviewDialog } from "@/components/ui/preview-dialog";
export function InteractiveExamples() {
  const [selected, setSelected] = useState<(typeof examples)[number] | null>(
    null,
  );
  const { t } = useLocale();
  return (
    <section className="section examples-section" id="examples">
      <div className="container">
        <SectionHeading
          title={t("من المفهوم .. إلى المثال")}
          description={t("أمثلة بسيطة تساعدك على طرح الأسئلة وربط الأفكار.")}
          icon={<Lightbulb size={27} />}
        />
        <div className="example-grid">
          {examples.map((example, i) => (
            <button
              className="example-card"
              key={example.id}
              onClick={() => setSelected(example)}
            >
              <div className="example-top">
                <span className="example-number">
                  {t("مثال")} <span dir="ltr">0{i + 1}</span>
                </span>
                <span className="example-level">{t("مبتدئ")}</span>
              </div>
              <div className="example-body">
                <span className="example-icon">
                  <ConceptIcon name={example.icon} />
                </span>
                <div>
                  <h3>{t(example.title)}</h3>
                  <p>{t(example.objective)}</p>
                </div>
              </div>
              <div className="example-bottom">
                <span className="example-tags">
                  {example.concepts.map((concept) => (
                    <span key={concept.ar}>{t(concept)}</span>
                  ))}
                </span>
                <span className="round-arrow">
                  <ArrowLeft size={16} aria-hidden="true" />
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
      {selected && (
        <PreviewDialog
          title={t(selected.title)}
          onClose={() => setSelected(null)}
        >
          <div className="scenario">
            <Scale size={25} aria-hidden="true" />
            <p>{t(selected.scenario)}</p>
          </div>
          <p>{t(selected.objective)}</p>
          <div className="dialog-question">
            <span>{t("المفاهيم التي تستكشفها")}</span>
            <p>{selected.concepts.join(" · ")}</p>
          </div>
          <p className="dialog-note">
            {t("هذا مثال تعليمي للتأمل، ولا يعرض حسابًا أو توزيعًا للتركة.")}
          </p>
          <a
            className="primary-button"
            href="#concepts"
            onClick={() => setSelected(null)}
          >
            {t("استكشف المفاهيم المرتبطة")}
            <ArrowLeft size={16} />
          </a>
        </PreviewDialog>
      )}
    </section>
  );
}
