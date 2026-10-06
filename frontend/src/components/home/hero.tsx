"use client";
import { useLocale } from "@/i18n/locale-context";
import Image from "next/image";
import { useState } from "react";
import { AskPanel } from "./ask-panel";
export function Hero() {
  const { t } = useLocale();
  const [active, setActive] = useState(false);
  const [workspace, setWorkspace] = useState<HTMLElement | null>(null);
  return (
    <div className="hero-experience" data-mode={active ? "active" : "idle"}>
      <section
        className="hero"
        data-mode={active ? "active" : "idle"}
        id="home"
        aria-labelledby="hero-title"
      >
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
            <div className="hero-intro-collapse" inert={active}>
              <div>
                <div className="hero-eyebrow">
                  <span />
                  <span>
                    {t({
                      ar: "معرفة تُنير، وحقوق تُصان",
                      en: "Knowledge that illuminates. Rights protected.",
                    })}
                  </span>
                </div>
                <h1 id="hero-title">
                  <span className="hero-invitation">
                    {t({ ar: "اسأل", en: "Ask" })}
                  </span>{" "}
                  <bdi lang="en" dir="ltr">
                    MAWARITH <span>AI</span>
                  </bdi>
                </h1>
                <h2>
                  {t({
                    ar: "إرشاد في علم المواريث، يجيبك بوضوح ويشرح لك الأحكام.",
                    en: "Clear guidance and explanations for Islamic inheritance.",
                  })}
                </h2>
                <p className="hero-description">
                  {t({
                    ar: "استنادًا إلى مصادر معتبرة، بلغة واضحة.",
                    en: "Grounded in trusted sources, explained in plain language.",
                  })}
                </p>
              </div>
            </div>
            <div className="hero-active-brand" aria-hidden={!active}>
              MAWARITH AI
            </div>
            <AskPanel workspace={workspace} onActiveChange={setActive} />
            <p className="hero-assurances">
              {t(
                "شرح موثوق بالمصادر • تعلّم يناسب مختلف المستويات • بالعربية والإنجليزية",
              )}
            </p>
          </div>
        </div>
        <div className="hero-bottom" aria-hidden="true" />
      </section>
      <section
        ref={setWorkspace}
        className="home-answer-workspace"
        hidden={!active}
        aria-label={t({ ar: "مساحة الإجابة", en: "Answer workspace" })}
      />
    </div>
  );
}
