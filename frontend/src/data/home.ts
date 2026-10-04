export type BilingualText = { ar: string; en: string };
export type Concept = {
  id: string;
  title: BilingualText;
  description: string;
  icon: "users" | "chart" | "tree" | "split" | "shield" | "layers" | "return";
  question: string;
};

export const concepts: Concept[] = [
  {
    id: "fixed-share-heirs",
    title: { ar: "أصحاب الفروض", en: "Fixed-share heirs" },
    description: "بداية التعرف على الورثة وأنصبتهم",
    icon: "users",
    question: "ما معنى أصحاب الفروض؟",
  },
  {
    id: "fixed-share",
    title: { ar: "الفرض", en: "Fixed share" },
    description: "فهم معنى النصيب المقدّر من التركة",
    icon: "chart",
    question: "ما معنى الفرض في المواريث؟",
  },
  {
    id: "residuary-heirs",
    title: { ar: "العصبة", en: "Residuary heirs" },
    description: "تعرّف على مفهوم الورثة بالعصوبة",
    icon: "tree",
    question: "ما معنى العصبة؟",
  },
  {
    id: "residuary-inheritance",
    title: { ar: "التعصيب", en: "Residuary inheritance" },
    description: "استكشف العلاقة بين الفروض والباقي",
    icon: "split",
    question: "ما الفرق بين الفرض والتعصيب؟",
  },
  {
    id: "blocking",
    title: { ar: "الحجب", en: "Blocking" },
    description: "كيف يؤثر وجود وارث في وارث آخر؟",
    icon: "shield",
    question: "ما معنى الحجب في المواريث؟",
  },
  {
    id: "awl",
    title: { ar: "العول", en: "Awl" },
    description: "مدخل إلى فهم تداخل الأنصبة",
    icon: "layers",
    question: "ما معنى العول؟",
  },
  {
    id: "radd",
    title: { ar: "الرد", en: "Radd" },
    description: "تعرّف على مفهوم الرد وشروطه",
    icon: "return",
    question: "ما معنى الرد في المواريث؟",
  },
];

export const examples = [
  {
    id: "wife-mother-children",
    title: "زوجة وأم وأبناء وبنت",
    scenario: "مات وترك زوجة وأمًا وابنين وبنتًا.",
    objective: "استكشف كيف تجتمع الفروض مع توزيع الباقي.",
    icon: "users" as const,
    concepts: ["الفرض", "التعصيب"],
  },
  {
    id: "wife-son-daughter",
    title: "زوجة وابن وبنت",
    scenario: "مات وترك زوجة وابنًا وبنتًا.",
    objective: "تعرّف على أثر وجود الأبناء في المسألة.",
    icon: "tree" as const,
    concepts: ["أصحاب الفروض", "العصبة"],
  },
  {
    id: "mother-son-daughters",
    title: "أم وابن وبنتان",
    scenario: "مات وترك أمًا وابنًا وبنتين.",
    objective: "ميّز بين نصيب المجموعة ونصيب الفرد.",
    icon: "chart" as const,
    concepts: ["الفرض", "التعصيب"],
  },
];

export const pathSteps = [
  "ما هو نظام المواريث؟",
  "الفرض وأصحاب الفروض",
  "العصبة والتعصيب",
  "الحجب وتفاعل القواعد",
  "تطبيق على مثال بسيط",
];
export const exampleQuestions = [
  "ما معنى أصحاب الفروض؟",
  "ما معنى العصبة؟",
  "ما الفرق بين الفرض والتعصيب؟",
];
