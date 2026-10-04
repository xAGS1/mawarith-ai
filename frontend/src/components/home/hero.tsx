"use client";
import { useLocale } from "@/i18n/locale-context";
import Image from "next/image";
import { AskPanel } from "./ask-panel";
export function Hero() {
  const { t } = useLocale();
  return (
    <section className="hero" id="home" aria-labelledby="hero-title">
      <Image
        className="hero-background"
        src="/assets/hero/mawarith-moonlit-hero.webp"
        alt=""
        aria-hidden="true"
        fill
        sizes="100vw"
        preload
      />
      <div className="container hero-inner">
        <div className="hero-copy">
          <div className="hero-eyebrow">
            <span />
            <span>{t("معرفةٌ تُنير .. وفهمٌ يُطمئن")}</span>
          </div>
          <h1 id="hero-title" lang="en" dir="ltr">
            MAWARITH <span>AI</span>
          </h1>
          <h2>
            {t("رحلتك لفهم علم المواريث")}
            <br />
            <span>{t("تبدأ بسؤال.")}</span>
          </h2>
          <p className="hero-description">
            {t("مساحة للتعلم والتأمل في مفاهيم المواريث في الإسلام.")}
            <br className="desktop-break" />
            {t("شرحٌ واضح، وخطواتٌ هادئة، ومصادرُ تستند إليها.")}
          </p>
          <AskPanel />
          <p className="hero-assurances">
            {t(
              "شرح موثوق بالمصادر • تعلّم يناسب مختلف المستويات • بالعربية والإنجليزية",
            )}
          </p>
        </div>
      </div>
      <div className="hero-bottom" aria-hidden="true" />
    </section>
  );
}
