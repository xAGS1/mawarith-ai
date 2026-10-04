"use client";
import { useLocale } from "@/i18n/locale-context";
import {
  BookOpen,
  LibraryBig,
  ScrollText,
  BookMarked,
  ArrowUpLeft,
} from "lucide-react";
import { SectionHeading } from "@/components/ui/section-heading";
const sources = [
  {
    name: "القرآن الكريم",
    description: "الآيات ذات الصلة بالمواريث",
    icon: BookOpen,
  },
  {
    name: "السنة النبوية",
    description: "التعرّف على مصادر السنة",
    icon: ScrollText,
  },
  {
    name: "الموسوعة الفقهية",
    description: "المفاهيم في سياقها الفقهي",
    icon: LibraryBig,
  },
  {
    name: "المراجع المعتمدة",
    description: "دليل قراءة واستزادة",
    icon: BookMarked,
  },
];
export function Sources() {
  const { t } = useLocale();
  return (
    <section className="section sources-section" id="sources">
      <div className="container">
        <SectionHeading
          title={t("للمعرفة أصول، وللفهم مصادر")}
          description={t(
            "تعرف على أبواب المعرفة التي يستند إليها علم المواريث.",
          )}
          icon={<LibraryBig size={27} />}
        />
        <div className="sources-grid">
          {sources.map(({ name, description, icon: Icon }) => (
            <div className="source-card" key={t(name)}>
              <Icon size={25} strokeWidth={1.5} aria-hidden="true" />
              <div>
                <h3>{t(name)}</h3>
                <p>{t(description)}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="source-note">
          <span>✦</span>
          <p>
            {t(
              "الفهم الدقيق يبدأ بالسياق. المسائل الشخصية تستدعي الرجوع إلى أهل الاختصاص.",
            )}
          </p>
          <a href="#about">
            {t("عن هذه المساحة")}
            <ArrowUpLeft size={14} aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}
