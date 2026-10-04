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

export const examples = [
  {
    id: "wife-mother-children",
    title: {
      ar: "زوجة وأم وأبناء وبنت",
      en: "Wife, mother, sons and daughter",
    },
    scenario: {
      ar: "مات وترك زوجة وأمًا وابنين وبنتًا.",
      en: "A man died leaving a wife, mother, two sons and a daughter.",
    },
    objective: {
      ar: "استكشف كيف تجتمع الفروض مع توزيع الباقي.",
      en: "Explore how fixed shares interact with distribution of the residue.",
    },
    icon: "users" as const,
    concepts: [
      { ar: "الفرض", en: "Fixed share" },
      { ar: "التعصيب", en: "Residuary inheritance" },
    ],
  },
  {
    id: "wife-son-daughter",
    title: { ar: "زوجة وابن وبنت", en: "Wife, son and daughter" },
    scenario: {
      ar: "مات وترك زوجة وابنًا وبنتًا.",
      en: "A man died leaving a wife, son and daughter.",
    },
    objective: {
      ar: "تعرّف على أثر وجود الأبناء في المسألة.",
      en: "Explore how children affect a case.",
    },
    icon: "tree" as const,
    concepts: [
      { ar: "أصحاب الفروض", en: "Fixed-share heirs" },
      { ar: "العصبة", en: "Residuary heirs" },
    ],
  },
  {
    id: "mother-son-daughters",
    title: { ar: "أم وابن وبنتان", en: "Mother, son and two daughters" },
    scenario: {
      ar: "مات وترك أمًا وابنًا وبنتين.",
      en: "A man died leaving a mother, son and two daughters.",
    },
    objective: {
      ar: "ميّز بين نصيب المجموعة ونصيب الفرد.",
      en: "Distinguish between a group's share and an individual's share.",
    },
    icon: "chart" as const,
    concepts: [
      { ar: "الفرض", en: "Fixed share" },
      { ar: "التعصيب", en: "Residuary inheritance" },
    ],
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
];

export type LearningPathDefinition = {
  id: string;
  title: BilingualText;
  subtitle: BilingualText;
  image: string;
  hoverText: BilingualText;
  slug: "beginner" | "intermediate" | "advanced" | "teachers-students";
};

export const learningPaths: LearningPathDefinition[] = [
  {
    id: "beginner-path",
    title: { ar: "المستوى المبتدئ", en: "Beginner" },
    subtitle: {
      ar: "المفاهيم الأساسية والقواعد",
      en: "Core concepts and foundational rules",
    },
    image: "/assets/learning-path/beginner.webp",
    hoverText: { ar: "ابدأ من الأساس", en: "Start with the basics" },
    slug: "beginner",
  },
  {
    id: "intermediate-path",
    title: { ar: "المستوى المتوسط", en: "Intermediate" },
    subtitle: {
      ar: "التطبيقات والمسائل المركبة",
      en: "Applied concepts and combined cases",
    },
    image: "/assets/learning-path/intermediate.webp",
    hoverText: { ar: "طبّق ما تعلمت", en: "Apply what you learned" },
    slug: "intermediate",
  },
  {
    id: "advanced-path",
    title: { ar: "المستوى المتقدم", en: "Advanced" },
    subtitle: {
      ar: "المسائل المعقدة وتفاعل القواعد",
      en: "Advanced cases and rule interaction",
    },
    image: "/assets/learning-path/advanced.webp",
    hoverText: { ar: "تعمّق أكثر", en: "Go deeper" },
    slug: "advanced",
  },
  {
    id: "teachers-students-path",
    title: { ar: "للمعلمين والطلاب", en: "Teachers & Students" },
    subtitle: {
      ar: "أدوات وموارد تعليمية",
      en: "Educational tools and learning resources",
    },
    image: "/assets/learning-path/teachers-students.webp",
    hoverText: { ar: "استكشف الموارد", en: "Explore resources" },
    slug: "teachers-students",
  },
];
