"use client";
import { useLocale } from "@/i18n/locale-context";
import { Route } from "lucide-react";
import { SectionHeading } from "@/components/ui/section-heading";
import { learningPaths } from "@/data/home";
import { LearningPathCard } from "./learning-path-card";
export function LearningPath() {
  const { t } = useLocale();
  return (
    <section className="section path-section" id="learning-path">
      <div className="container">
        <SectionHeading
          title={t("خطوة بخطوة .. إلى وضوح أكبر")}
          description={t("مسار واحد، بداية بسيطة. تعلم بالترتيب الذي يناسبك.")}
          icon={<Route size={27} />}
        />
        <div className="learning-path-catalog">
          {learningPaths.map((path) => (
            <LearningPathCard key={path.id} path={path} />
          ))}
        </div>
      </div>
    </section>
  );
}
