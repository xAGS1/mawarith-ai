"use client";
import Link from "next/link";
import { Navbar } from "@/components/layout/navbar";
import { Footer } from "@/components/layout/footer";
import { useLocale } from "@/i18n/locale-context";
import type { LearningPathDefinition } from "@/data/home";

export function PathShell({ path }: { path: LearningPathDefinition }) {
  const { t } = useLocale();
  return (
    <>
      <Navbar homeLinks />
      <main id="main" className="section path-shell">
        <div className="container">
          <h1>{t(path.title)}</h1>
          <p>{t(path.subtitle)}</p>
          <p>
            {t({
              ar: "هيكل المسار جاهز لدمج المحتوى التعليمي. لم تُضف الدروس بعد.",
              en: "The path structure is ready for educational content integration. Lessons have not been added yet.",
            })}
          </p>
          <Link href="/#learning-path">
            {t({
              ar: "العودة إلى مسارات التعلم",
              en: "Back to Learning Paths",
            })}
          </Link>
        </div>
      </main>
      <Footer homeLinks />
    </>
  );
}
