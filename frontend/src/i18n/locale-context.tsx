"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import english from "./en.json";
import type { BilingualText } from "@/data/home";

export type Locale = "ar" | "en";
const storageKey = "mawarith-locale";
const LocaleContext = createContext<{
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (text: string | BilingualText) => string;
} | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, updateLocale] = useState<Locale>("ar");
  useEffect(() => {
    try {
      if (localStorage.getItem(storageKey) === "en") updateLocale("en");
    } catch {
      /* Storage may be disabled; switching still works. */
    }
  }, []);
  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    document.title =
      locale === "ar"
        ? "MAWARITH AI | رحلة لفهم علم المواريث"
        : "MAWARITH AI | Understanding Islamic Inheritance";
  }, [locale]);
  const setLocale = (next: Locale) => {
    updateLocale(next);
    try {
      localStorage.setItem(storageKey, next);
    } catch {
      /* Optional persistence. */
    }
  };
  const t = (text: string | BilingualText): string => {
    if (typeof text !== "string") return text[locale];
    return locale === "ar"
      ? text
      : ((english as Record<string, string>)[text] ?? text);
  };
  return (
    <LocaleContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const value = useContext(LocaleContext);
  if (!value) throw new Error("useLocale must be used within LocaleProvider");
  return value;
}

export function SkipLink() {
  const { t } = useLocale();
  return (
    <a href="#main" className="skip-link">
      {t("انتقل إلى المحتوى")}
    </a>
  );
}
