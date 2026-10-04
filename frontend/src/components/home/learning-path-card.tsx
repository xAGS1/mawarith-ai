"use client";
import { useState } from "react";
import Image from "next/image";
import { ArrowLeft } from "lucide-react";
import { useLocale } from "@/i18n/locale-context";
import type { LearningPathDefinition } from "@/data/home";
export function LearningPathCard({ path }: { path: LearningPathDefinition }) {
  const [expanded, setExpanded] = useState(false);
  const { t } = useLocale();
  return (
    <div className="learning-card">
      <div className="path-illustration">
        <Image
          src={path.image}
          alt=""
          aria-hidden="true"
          fill
          sizes="(max-width: 600px) 100vw, (max-width: 2200px) 30vw, 1200px"
          className="path-nook-image"
        />
      </div>
      <div className="path-content">
        <span className="level-badge">
          <span />
          {t(path.level)}
        </span>
        <h3>{t(path.title)}</h3>
        <p>{t(path.subtitle)}</p>
        <div className="path-details">
          <button
            type="button"
            className="path-toggle"
            aria-expanded={expanded}
            aria-controls={`${path.id}-steps`}
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? t("إخفاء المسار") : t("استكشف المسار")}
            <ArrowLeft size={17} aria-hidden="true" />
          </button>
          <div
            className="path-expansion"
            data-expanded={expanded}
            aria-hidden={!expanded}
            inert={!expanded}
            id={`${path.id}-steps`}
          >
            <div className="path-expansion-inner">
              <ol>
                {path.steps.map((step, i) => (
                  <li key={step.title.ar}>
                    <span>{i + 1}</span>
                    <a href={step.href}>{t(step.title)}</a>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
