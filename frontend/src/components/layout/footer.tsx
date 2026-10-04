"use client";
import { useLocale } from "@/i18n/locale-context";
import { ArrowUp } from "lucide-react";
import { Brand } from "@/components/ui/brand";
export function Footer() {
  const { t } = useLocale();
  return (
    <footer className="footer" id="about">
      <div className="container footer-main">
        <div>
          <Brand compact />
          <p className="footer-description">
            {t("مساحة تعليمية لفهم علم المواريث في الإسلام.")}
            <br />
            {t("للجميع، مهما كانت خلفيتك أو نقطة بدايتك.")}
          </p>
        </div>
        <div className="footer-links">
          <a href="#concepts">{t("استكشف المفاهيم")}</a>
          <a href="#learning-path">{t("المسار التعليمي")}</a>
          <a href="#examples">{t("الأمثلة")}</a>
          <a href="#sources">{t("المصادر")}</a>
        </div>
        <div className="footer-quote">
          {t("بالعلم، نفهم.")}
          <br />
          <span>{t("وبالفهم، نطمئن.")}</span>
        </div>
      </div>
      <div className="container footer-bottom">
        <p>
          <span lang="en" dir="ltr">
            © 2026 MAWARITH AI
          </span>{" "}
          {t("— صُمّم من أجل الفهم")}
        </p>
        <span>{t("التعلم أولًا .. والحساب خطوة تالية")}</span>
        <a href="#home" aria-label={t("العودة إلى أعلى الصفحة")}>
          <ArrowUp size={17} />
        </a>
      </div>
    </footer>
  );
}
