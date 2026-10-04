"use client";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { useLocale } from "@/i18n/locale-context";
import type { LearningPathDefinition } from "@/data/home";

export function LearningPathCard({ path }: { path: LearningPathDefinition }) {
  const { t } = useLocale();
  return (
    <article
      className="learning-card"
      data-path={path.slug}
      aria-labelledby={`${path.id}-title`}
    >
      <div className="path-illustration">
        <Image
          src={path.image}
          alt=""
          aria-hidden="true"
          fill
          sizes="(max-width: 600px) 100vw, (max-width: 1100px) 50vw, (max-width: 2200px) 25vw, 900px"
          className="path-nook-image"
        />
      </div>
      <div className="path-content">
        <h3 id={`${path.id}-title`}>{t(path.title)}</h3>
        <p>{t(path.subtitle)}</p>
        <Link
          className="path-toggle"
          href={`/learn/paths/${path.slug}`}
          prefetch={false}
        >
          {t("استكشف المسار")}
          <ArrowLeft size={17} aria-hidden="true" />
          <span className="path-hover-copy" aria-hidden="true">
            {t(path.hoverText)}
          </span>
        </Link>
      </div>
    </article>
  );
}
