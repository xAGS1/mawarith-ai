import type { Metadata } from "next";
import "@fontsource-variable/noto-sans-arabic";
import "@fontsource/amiri/400.css";
import "@fontsource/amiri/700.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "MAWARITH AI | رحلة لفهم علم المواريث",
  description:
    "مساحة تعليمية لفهم مفاهيم المواريث في الإسلام، بخطوات واضحة ومصادر موثوقة.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <a href="#main" className="skip-link">
          انتقل إلى المحتوى
        </a>
        {children}
      </body>
    </html>
  );
}
