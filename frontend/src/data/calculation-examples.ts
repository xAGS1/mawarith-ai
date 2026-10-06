export const calculationExamples = [
  {
    id: "direct",
    icon: "balance",
    number: "01",
    badge: { ar: "مباشر", en: "Direct" },
    title: { ar: "توزيع مباشر", en: "Direct distribution" },
    caseLabel: { ar: "زوجة + ابن + بنت", en: "Wife + son + daughter" },
    description: {
      ar: "حالة واضحة لاختبار فهم الورثة وتوزيع الأنصبة.",
      en: "A clear case to explore heir understanding and share distribution.",
    },
    cta: { ar: "ابدأ الحالة", en: "Start the case" },
    question: {
      ar: "توفي رجل وترك زوجة وابنًا وبنتًا.",
      en: "A man died leaving a wife, a son and a daughter.",
    },
  },
  {
    id: "connected",
    icon: "rules",
    number: "02",
    badge: { ar: "متعدد القواعد", en: "Multiple rules" },
    title: { ar: "قواعد مترابطة", en: "Connected rules" },
    caseLabel: {
      ar: "زوجة + أم + ابنان + بنت",
      en: "Wife + mother + two sons + daughter",
    },
    description: {
      ar: "مسألة تجمع أكثر من قاعدة وتوضح كيف يبني النظام النتيجة خطوة بخطوة.",
      en: "A case combining several rules, showing how the system builds the result step by step.",
    },
    cta: { ar: "استكشف الحساب", en: "Explore the calculation" },
    question: {
      ar: "توفي رجل وترك زوجة وأمًا وابنين وبنتًا.",
      en: "A man died leaving a wife, a mother, two sons and a daughter.",
    },
  },
  {
    id: "clarification",
    icon: "question",
    number: "03",
    badge: { ar: "يحتاج استيضاح", en: "Needs clarification" },
    title: { ar: "قبل أن نحسب", en: "Before calculating" },
    caseLabel: { ar: "بنت + أخ", en: "Daughter + brother" },
    description: {
      ar: "حالة توضّح متى يطلب MAWARITH استيضاحًا بدل أن يفترض معلومة غير موجودة.",
      en: "See when MAWARITH requests clarification instead of assuming missing information.",
    },
    cta: { ar: "اختبر الاستيضاح", en: "Try clarification" },
    question: {
      ar: "توفي رجل وترك بنتًا وأخًا.",
      en: "A man died leaving a daughter and a brother.",
    },
  },
] as const;
