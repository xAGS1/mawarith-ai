import {
  curriculum,
  conceptEvidence,
  awlExample,
  type CurriculumSlug,
} from "./concept-curriculum";
import { calculationExamples } from "./calculation-examples";
import type { BilingualText } from "./home";
import rules from "./calculation-evidence.json";
const bi = (ar: string, en: string): BilingualText => ({ ar, en });
const definition = (slug: CurriculumSlug) =>
  curriculum.find((c) => c.slug === slug)!.definition;
const paths = [
  {
    slug: "fixed-shares",
    order: 1,
    title: bi("الفروض", "Fixed shares"),
    description: bi(
      "تبدأ بعض المسائل بأنصبة مقدرة لورثة محددين.",
      "Some cases begin with prescribed shares for particular heirs.",
    ),
    cta: bi("افهم الطريقة", "Understand the method"),
    intro: definition("fixed-share"),
    steps: [
      bi("فهم الحالة", "Understand the case"),
      bi("تحديد الورثة", "Identify heirs"),
      bi("تحديد صاحب الفرض", "Identify the fixed-share heir"),
      bi("تطبيق النصيب المقدر", "Apply the prescribed share"),
      bi("التحقق من النتيجة", "Verify the result"),
    ],
    relatedConcepts: ["fixed-share", "tasib"] as CurriculumSlug[],
    sources: [conceptEvidence["fixed-share"]],
    ruleSummaries: [rules[0]],
    example: calculationExamples[0].question,
    explanation: [
      bi(
        "نقرأ الحالة ونحدد الزوجة والابن والبنت.",
        "Read the case and identify the wife, son and daughter.",
      ),
      bi(
        rules[0].rule,
        "The wife or wives together receive one eighth when the deceased has a child.",
      ),
      bi(
        "هذا المسار يركز على الفرض؛ معالجة الباقي تأتي في المسار التالي. يتحقق النظام من التوزيع عند الطلب.",
        "This path focuses on the fixed share; the next path considers the remainder. The system verifies distribution when requested.",
      ),
    ],
    tryCase: calculationExamples[0].question,
    conceptual: false,
  },
  {
    slug: "shares-and-tasib",
    order: 2,
    title: bi("الفروض والتعصيب", "Fixed shares & residuary inheritance"),
    description: bi(
      "تُعطى الفروض أولًا، ثم يُنظر في الباقي للعصبة.",
      "Fixed shares are allocated first, then the remainder is considered for residuary heirs.",
    ),
    cta: bi("شاهد الخطوات", "See the steps"),
    intro: definition("asabah"),
    steps: [
      bi("تحديد الورثة", "Identify heirs"),
      bi("تحديد الفروض وإعطاؤها", "Identify and allocate fixed shares"),
      bi("تحديد الباقي", "Identify the remainder"),
      bi("تطبيق التعصيب", "Apply residuary inheritance"),
      bi("التحقق", "Verify"),
    ],
    relatedConcepts: ["fixed-share", "tasib", "asabah"] as CurriculumSlug[],
    sources: [conceptEvidence.tasib, conceptEvidence.asabah],
    ruleSummaries: rules,
    example: calculationExamples[1].question,
    explanation: [
      bi(
        rules[0].rule,
        "The wife or wives together receive one eighth when the deceased has a child.",
      ),
      bi(rules[1].rule, "The mother receives one sixth when there is a child."),
      bi(
        rules[2].rule,
        "Sons and daughters share the remainder after fixed shares, with each male receiving twice each female's share.",
      ),
      bi(
        "يحسب النظام التوزيع ويتحقق منه عند إرسال الحالة، وليس عند فتح الصفحة.",
        "The system calculates and verifies distribution when the case is submitted, not when this page opens.",
      ),
    ],
    tryCase: calculationExamples[1].question,
    conceptual: false,
  },
  {
    slug: "awl",
    order: 3,
    title: bi("العَول", "Awl"),
    description: bi(
      "عندما تزيد سهام أصحاب الفروض على أصل المسألة.",
      "When fixed-share allocations exceed the case origin.",
    ),
    cta: bi("افهم العَول", "Understand awl"),
    intro: definition("awl"),
    steps: [
      bi("تحديد الفروض", "Identify fixed shares"),
      bi("جمع السهام", "Add the shares"),
      bi("السهام تتجاوز الأصل", "Shares exceed the origin"),
      bi("يرتفع أصل المسألة", "The case origin increases"),
      bi(
        "قراءة النسب على الأصل الجديد",
        "Read the proportions using the new origin",
      ),
    ],
    relatedConcepts: ["fixed-share", "awl"] as CurriculumSlug[],
    sources: [conceptEvidence.awl, conceptEvidence["awl-example"]],
    ruleSummaries: [],
    example: awlExample.scenario,
    explanation: [awlExample.explanation],
    tryCase: bi(
      "توفي رجل وترك زوجة وبنتين وأمًا وأبًا.",
      "A man died leaving a wife, two daughters, a mother and a father.",
    ),
    conceptual: false,
  },
  {
    slug: "radd",
    order: 4,
    title: bi("الرَّد", "Radd"),
    description: bi(
      "عندما يبقى جزء من التركة بعد أصحاب الفروض وفق الحالة المعتبرة.",
      "When part of the estate remains after fixed shares in the applicable case.",
    ),
    cta: bi("افهم الرَّد", "Understand radd"),
    intro: definition("radd"),
    steps: [
      bi("تحديد الفروض", "Identify fixed shares"),
      bi("توزيع الفروض", "Allocate fixed shares"),
      bi("وجود فائض", "A surplus remains"),
      bi(
        "لا يوجد مستحق من العصبات في الحالة المعتبرة",
        "No entitled residuary heir in the applicable case",
      ),
      bi(
        "معالجة الرد وفق القاعدة المعتمدة",
        "Handle radd under the approved rule",
      ),
    ],
    relatedConcepts: ["fixed-share", "asabah", "radd"] as CurriculumSlug[],
    sources: [conceptEvidence.radd],
    ruleSummaries: [],
    example: bi(
      "بقاء مال بعد الفروض، مع عدم وجود مستحق له من العصبات، كما يقيد التعريف المنقول.",
      "Estate remains after fixed shares, with no entitled residuary heir, as qualified in the cited definition.",
    ),
    explanation: [
      definition("radd"),
      bi(
        "نكتفي بالتسلسل المفاهيمي؛ لا نعرض مثالًا عدديًا جديدًا ولا نعمم أحكام الرد بين المذاهب.",
        "This is a conceptual sequence; no new numerical example or universal rule across schools is presented.",
      ),
    ],
    tryCase: bi(
      "توفي رجل وترك بنتًا فقط.",
      "A man died leaving only a daughter.",
    ),
    conceptual: true,
  },
];
export const calculationPaths = paths.map((path, index) => ({
  ...path,
  previous: paths[index - 1]?.slug,
  next: paths[index + 1]?.slug,
}));
export type CalculationPath = (typeof calculationPaths)[number];
