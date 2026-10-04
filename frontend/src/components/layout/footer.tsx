"use client";
import { useLocale } from "@/i18n/locale-context";
import { ArrowUp } from "lucide-react";
import { Brand } from "@/components/ui/brand";
export function Footer({ homeLinks = false }: { homeLinks?: boolean }) {
  const { t } = useLocale();
  const target = (hash: string) => (homeLinks ? `/${hash}` : hash);
  return (
    <footer className="footer" id="about">
      <div className="container footer-main">
        <div>
          <Brand compact href={target("#home")} />
          <p className="footer-description">
            {t("مساحة تعليمية لفهم علم المواريث في الإسلام.")}
            <br />
            {t("للجميع، مهما كانت خلفيتك أو نقطة بدايتك.")}
          </p>
        </div>
        <div className="footer-links">
          <a href={target("#concepts")}>{t("استكشف المفاهيم")}</a>
          <a href={target("#learning-path")}>{t("المسار التعليمي")}</a>
          <a href={target("#examples")}>{t("الأمثلة")}</a>
          <a href={target("#sources")}>{t("المصادر")}</a>
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
        <a href={target("#home")} aria-label={t("العودة إلى أعلى الصفحة")}>
          <ArrowUp size={17} />
        </a>
      </div>
    </footer>
  );
}
