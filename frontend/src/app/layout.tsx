import type { Metadata } from "next";
import "@fontsource-variable/noto-sans-arabic";
import "@fontsource/amiri/400.css";
import "@fontsource/amiri/700.css";
import "./globals.css";
import { LocaleProvider, SkipLink } from "@/i18n/locale-context";
import { AskRequestProvider } from "@/lib/ask/ask-request-provider";

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
        <LocaleProvider>
          <SkipLink />
          <AskRequestProvider>{children}</AskRequestProvider>
        </LocaleProvider>
      </body>
    </html>
  );
}
