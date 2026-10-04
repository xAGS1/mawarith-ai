"use client";
import { useState } from "react";
import { ArrowLeft, BookOpenText } from "lucide-react";
import { concepts, type Concept } from "@/data/home";
import { ConceptIcon } from "@/components/ui/icons";
import { SectionHeading } from "@/components/ui/section-heading";
import { PreviewDialog } from "@/components/ui/preview-dialog";
export function ConceptCards() {
  const [selected, setSelected] = useState<Concept | null>(null);
  return (
    <section className="section concepts-section" id="concepts">
      <div className="container">
        <SectionHeading
          title="مفاهيم صغيرة، فهم أعمق"
          description="ابدأ من الأساسيات. كل مفهوم يفتح لك بابًا جديدًا للفهم."
          icon={<BookOpenText size={27} />}
          href="#learning-path"
          linkText="ابدأ مسارك التعليمي"
        />
        <div className="concept-grid">
          {concepts.map((concept, i) => (
            <button
              key={concept.id}
              className="concept-card"
              onClick={() => setSelected(concept)}
            >
              <span className="concept-index" dir="ltr">
                0{i + 1}
              </span>
              <ConceptIcon name={concept.icon} className="concept-icon" />
              <h3>{concept.title.ar}</h3>
              <p>{concept.description}</p>
              <span className="card-discover">
                اكتشف المفهوم <ArrowLeft size={14} aria-hidden="true" />
              </span>
            </button>
          ))}
        </div>
      </div>
      {selected && (
        <PreviewDialog
          title={selected.title.ar}
          onClose={() => setSelected(null)}
        >
          <p>{selected.description}</p>
          <div className="dialog-question">
            <span>سؤال تبدأ به</span>
            <p>{selected.question}</p>
          </div>
          <p className="dialog-note">
            بطاقة استكشافية في المعاينة التعليمية. لا تتضمن حكمًا لحالة شخصية.
          </p>
          <a
            href="#home"
            className="primary-button"
            onClick={() => setSelected(null)}
          >
            العودة إلى مساحة السؤال <ArrowLeft size={16} />
          </a>
        </PreviewDialog>
      )}
    </section>
  );
}
