"use client";
import { useState } from "react";
import { BookOpen, Scale, LibraryBig, Menu, X, Globe2 } from "lucide-react";
import { Brand } from "@/components/ui/brand";
const links = [
  { label: "الرئيسية", href: "#home" },
  { label: "وضع التعلم", href: "#concepts", icon: BookOpen },
  { label: "وضع المسائل", href: "#examples", icon: Scale },
  { label: "المصادر", href: "#sources", icon: LibraryBig },
  { label: "عن المشروع", href: "#about" },
];
export function Navbar() {
  const [open, setOpen] = useState(false);
  const [languageNotice, setLanguageNotice] = useState(false);
  return (
    <header className="navbar">
      <div className="container nav-inner">
        <Brand />
        <nav
          id="mobile-nav"
          className={open ? "nav-links is-open" : "nav-links"}
          aria-label="التنقل الرئيسي"
        >
          {links.map(({ label, href, icon: Icon }, i) => (
            <a
              key={href}
              href={href}
              className={i === 0 ? "nav-active" : ""}
              onClick={() => setOpen(false)}
            >
              {Icon && <Icon size={16} aria-hidden="true" />}
              {label}
            </a>
          ))}
        </nav>
        <div className="nav-actions">
          <div className="language-wrap">
            <button
              className="language-button"
              onClick={() => setLanguageNotice(!languageNotice)}
              aria-expanded={languageNotice}
              aria-controls="language-notice"
            >
              <Globe2 size={17} aria-hidden="true" />
              <span>العربية</span>
              <span className="language-short" lang="en">
                AR
              </span>
            </button>
            {languageNotice && (
              <p id="language-notice" className="language-notice" role="status">
                النسخة الإنجليزية قريبًا
              </p>
            )}
          </div>
          <button
            className="menu-toggle"
            aria-label={open ? "إغلاق القائمة" : "فتح القائمة"}
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
