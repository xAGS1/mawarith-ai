import { ShieldCheck, Sparkles } from "lucide-react";
import { AskPanel } from "./ask-panel";
import { MoonlitScene } from "./moonlit-scene";
export function Hero() {
  return (
    <section className="hero" id="home" aria-labelledby="hero-title">
      <div className="hero-pattern" aria-hidden="true" />
      <div className="container hero-inner">
        <div className="hero-copy">
          <div className="hero-eyebrow">
            <span />
            <span>معرفةٌ تُنير .. وفهمٌ يُطمئن</span>
          </div>
          <h1 id="hero-title" lang="en" dir="ltr">
            MAWARITH <span>AI</span>
          </h1>
          <h2>
            رحلتك لفهم علم المواريث
            <br />
            <span>تبدأ بسؤال.</span>
          </h2>
          <p className="hero-description">
            مساحة للتعلم والتأمل في مفاهيم المواريث في الإسلام.
            <br className="desktop-break" /> شرحٌ واضح، وخطواتٌ هادئة، ومصادرُ
            تستند إليها.
          </p>
          <AskPanel />
          <div className="hero-assurances">
            <span>
              <ShieldCheck size={16} aria-hidden="true" />
              المعرفة من مصادرها
            </span>
            <i />
            <span>
              <Sparkles size={15} aria-hidden="true" />
              تعلم يناسب الجميع
            </span>
            <span className="preview-badge">معاينة تعليمية</span>
          </div>
        </div>
        <div className="hero-art">
          <MoonlitScene />
          <div className="art-caption">
            <span className="ornament">✦</span> للعلم أبواب .. وللفهم مفاتيح{" "}
            <span className="ornament">✦</span>
          </div>
        </div>
      </div>
      <div className="hero-bottom" aria-hidden="true" />
    </section>
  );
}
