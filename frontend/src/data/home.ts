import { learningPathCurriculum } from "./learning-paths";
export type BilingualText = { ar: string; en: string };
export type Concept = {
  id: string;
  title: BilingualText;
  description: BilingualText;
  icon: "users" | "chart" | "tree" | "split" | "shield" | "layers" | "return";
  question: BilingualText;
};

export const concepts: Concept[] = [
  {
    id: "fixed-share-heirs",
    title: { ar: "أصحاب الفروض", en: "Fixed-share heirs" },
    description: {
      ar: "بداية التعرف على الورثة وأنصبتهم",
      en: "An introduction to heirs and their shares",
    },
    icon: "users",
    question: {
      ar: "ما معنى أصحاب الفروض؟",
      en: "What are fixed-share heirs?",
    },
  },
  {
    id: "fixed-share",
    title: { ar: "الفرض", en: "Fixed share" },
    description: {
      ar: "فهم معنى النصيب المقدّر من التركة",
      en: "Explore the meaning of a prescribed estate share",
    },
    icon: "chart",
    question: {
      ar: "ما معنى الفرض في المواريث؟",
      en: "What is a fixed share in inheritance?",
    },
  },
  {
    id: "residuary-heirs",
    title: { ar: "العصبة", en: "Residuary heirs" },
    description: {
      ar: "تعرّف على مفهوم الورثة بالعصوبة",
      en: "Explore the concept of residuary heirs",
    },
    icon: "tree",
    question: { ar: "ما معنى العصبة؟", en: "What is a residuary heir?" },
  },
  {
    id: "residuary-inheritance",
    title: { ar: "التعصيب", en: "Residuary inheritance" },
    description: {
      ar: "استكشف العلاقة بين الفروض والباقي",
      en: "Explore the relationship between fixed shares and the residue",
    },
    icon: "split",
    question: {
      ar: "ما الفرق بين الفرض والتعصيب؟",
      en: "How do fixed shares and residuary inheritance differ?",
    },
  },
  {
    id: "blocking",
    title: { ar: "الحجب", en: "Blocking" },
    description: {
      ar: "كيف يؤثر وجود وارث في وارث آخر؟",
      en: "How can one heir affect another?",
    },
    icon: "shield",
    question: {
      ar: "ما معنى الحجب في المواريث؟",
      en: "What is blocking in inheritance?",
    },
  },
  {
    id: "awl",
    title: { ar: "العول", en: "Awl" },
    description: {
      ar: "مدخل إلى فهم تداخل الأنصبة",
      en: "An introduction to interacting shares",
    },
    icon: "layers",
    question: { ar: "ما معنى العول؟", en: "What is awl?" },
  },
  {
    id: "radd",
    title: { ar: "الرد", en: "Radd" },
    description: {
      ar: "تعرّف على مفهوم الرد وشروطه",
      en: "Explore the concept of radd and its conditions",
    },
    icon: "return",
    question: {
      ar: "ما معنى الرد في المواريث؟",
      en: "What is radd in inheritance?",
    },
  },
];

export const pathSteps = [
  { ar: "ما هو نظام المواريث؟", en: "What is Islamic inheritance?" },
  { ar: "الفرض وأصحاب الفروض", en: "Fixed shares and fixed-share heirs" },
  { ar: "العصبة والتعصيب", en: "Residuary heirs and inheritance" },
  { ar: "الحجب وتفاعل القواعد", en: "Blocking and interacting rules" },
  { ar: "تطبيق على مثال بسيط", en: "Explore a simple example" },
];
export const exampleQuestions = [
  concepts[0].question,
  concepts[2].question,
  concepts[3].question,
  concepts[5].question,
  {
    ar: "توفي رجل وترك زوجة وأم وابنين وبنت",
    en: "A man died leaving a wife, mother, two sons and a daughter",
  },
];

export type LearningPathDefinition = {
  id: string;
  title: BilingualText;
  subtitle: BilingualText;
  image: string;
  hoverText: BilingualText;
  slug:
    | "inheritance-foundations"
    | "shares-rules"
    | "cases-applications"
    | "special-advanced";
};

export const learningPaths: LearningPathDefinition[] =
  learningPathCurriculum.map((path) => ({
    id: path.slug + "-path",
    title: path.title,
    subtitle: path.subtitle,
    image: path.image,
    hoverText: path.hoverText,
    slug: path.slug,
  }));
