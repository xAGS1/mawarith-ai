"use client";
import { useLocale } from "@/i18n/locale-context";
export function Brand({ compact = false }: { compact?: boolean }) {
  const { t } = useLocale();
  return (
    <a
      href="#home"
      className={`brand ${compact ? "brand-small" : ""}`}
      aria-label={t("مواريث — الرئيسية")}
    >
      <svg
        viewBox="0 0 44 56"
        className="brand-mark"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M5 49V27C5 16 16 15 22 4c6 11 17 12 17 23v22M10 49V29c0-8 8-11 12-18 4 7 12 10 12 18v20"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path
          d="M17 47V31h10v16M14 47h16M12 51h20"
          stroke="currentColor"
          strokeWidth="1.4"
        />
        <path d="M25 23a5 5 0 1 1-6-7 5 5 0 0 0 6 7Z" fill="currentColor" />
      </svg>
      <span>
        <span className="brand-name" lang="en" dir="ltr">
          MAWARITH <span>AI</span>
        </span>
        <span className="brand-caption">{t("علمٌ يُفهم .. وحقوقٌ تُصان")}</span>
      </span>
    </a>
  );
}
