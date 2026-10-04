"use client";
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
  return (
    <section className="section examples-section" id="examples">
      <div className="container">
        <SectionHeading
          title="من المفهوم .. إلى المثال"
          description="أمثلة بسيطة تساعدك على طرح الأسئلة وربط الأفكار."
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
                  مثال <span dir="ltr">0{i + 1}</span>
                </span>
                <span className="example-level">مبتدئ</span>
              </div>
              <div className="example-body">
                <span className="example-icon">
                  <ConceptIcon name={example.icon} />
                </span>
                <div>
                  <h3>{example.title}</h3>
                  <p>{example.objective}</p>
                </div>
              </div>
              <div className="example-bottom">
                <span>{example.concepts.join(" · ")}</span>
                <span className="round-arrow">
                  <ArrowLeft size={16} aria-hidden="true" />
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
      {selected && (
        <PreviewDialog title={selected.title} onClose={() => setSelected(null)}>
          <div className="scenario">
            <Scale size={25} aria-hidden="true" />
            <p>{selected.scenario}</p>
          </div>
          <p>{selected.objective}</p>
          <div className="dialog-question">
            <span>المفاهيم التي تستكشفها</span>
            <p>{selected.concepts.join(" · ")}</p>
          </div>
          <p className="dialog-note">
            هذا مثال تعليمي للتأمل، ولا يعرض حسابًا أو توزيعًا للتركة.
          </p>
          <a
            className="primary-button"
            href="#concepts"
            onClick={() => setSelected(null)}
          >
            استكشف المفاهيم المرتبطة <ArrowLeft size={16} />
          </a>
        </PreviewDialog>
      )}
    </section>
  );
}
