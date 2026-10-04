"use client";
import { useLocale } from "@/i18n/locale-context";
import { useEffect, useState } from "react";
import {
  BookOpen,
  Route,
  Scale,
  LibraryBig,
  Menu,
  X,
  Globe2,
} from "lucide-react";
import { Brand } from "@/components/ui/brand";
const links = [
  { label: "الرئيسية", href: "#home" },
  { label: "المفاهيم", href: "#concepts", icon: BookOpen },
  { label: "مسارات التعلم", href: "#learning-path", icon: Route },
  { label: "الأمثلة", href: "#examples", icon: Scale },
  { label: "المصادر", href: "#sources", icon: LibraryBig },
  { label: "عن المشروع", href: "#about" },
];
export function Navbar({ homeLinks = false }: { homeLinks?: boolean }) {
  const [open, setOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("home");
  const { t, locale, setLocale } = useLocale();
  useEffect(() => {
    const sections = [
      "home",
      "concepts",
      "learning-path",
      "examples",
      "sources",
      "about",
    ]
      .map((id) => document.getElementById(id))
      .filter((section): section is HTMLElement => section !== null);
    const updateActiveSection = () => {
      const visible = sections.filter((section) => {
        const bounds = section.getBoundingClientRect();
        return bounds.bottom > 0 && bounds.top < window.innerHeight;
      });
      const atEnd =
        Math.ceil(window.scrollY + window.innerHeight) >=
        document.documentElement.scrollHeight;
      const selected = atEnd
        ? visible.at(-1)
        : (visible.find((section) => {
            const bounds = section.getBoundingClientRect();
            return (
              bounds.top <= window.innerHeight / 4 &&
              bounds.bottom > window.innerHeight / 4
            );
          }) ?? visible[0]);
      if (selected) setActiveSection(selected.id);
    };
    const observer = new IntersectionObserver(updateActiveSection, {
      threshold: [0, 0.1, 0.25, 0.5, 0.75, 1],
    });
    sections.forEach((section) => observer.observe(section));
    updateActiveSection();
    return () => observer.disconnect();
  }, []);
  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Brand href={homeLinks ? "/#home" : "#home"} />
        <nav
          id="mobile-nav"
          className={open ? "nav-links is-open" : "nav-links"}
          aria-label={t("التنقل الرئيسي")}
        >
          {links.map(({ label, href, icon: Icon }) => (
            <a
              key={href}
              href={homeLinks ? `/${href}` : href}
              className={
                !homeLinks && href === `#${activeSection}` ? "nav-active" : ""
              }
              aria-current={
                !homeLinks && href === `#${activeSection}`
                  ? "location"
                  : undefined
              }
              onClick={() => setOpen(false)}
            >
              {Icon && <Icon size={16} aria-hidden="true" />}
              {t(label)}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <div className="language-wrap">
            <button
              className="language-button"
              onClick={() => setLocale(locale === "ar" ? "en" : "ar")}
              aria-label={
                locale === "ar" ? "Switch to English" : "التبديل إلى العربية"
              }
            >
              <Globe2 size={17} aria-hidden="true" />
              <span className="language-code" lang="en" dir="ltr">
                AR / EN
              </span>
            </button>
          </div>
          <button
            className="menu-toggle"
            aria-label={open ? t("إغلاق القائمة") : t("فتح القائمة")}
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen(!open)}
          >
            {open ? <X /> : <Menu />}
          </button>
        </div>
      </div>
    </header>
  );
}
