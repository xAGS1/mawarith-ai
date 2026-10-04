"use client";
import Image from "next/image";
import { useLocale } from "@/i18n/locale-context";
export function Brand({
  compact = false,
  href = "#home",
}: {
  compact?: boolean;
  href?: string;
}) {
  const { t } = useLocale();
  return (
    <a
      href={href}
      className={`brand ${compact ? "brand-small" : ""}`}
      aria-label={t("مواريث — الرئيسية")}
    >
      <Image
        src="/assets/logo/logo2.png"
        width={46}
        height={46}
        sizes={compact ? "40px" : "(max-width: 600px) 38px, 46px"}
        alt=""
        aria-hidden="true"
        className="brand-mark"
      />
      <span>
        <span className="brand-name" lang="en" dir="ltr">
          MAWARITH <span>AI</span>
        </span>
        <span className="brand-caption">{t("علمٌ يُفهم .. وحقوقٌ تُصان")}</span>
      </span>
    </a>
  );
}
