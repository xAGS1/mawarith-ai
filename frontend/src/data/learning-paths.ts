import type { BilingualText } from "./home";

const bi = (ar: string, en: string): BilingualText => ({ ar, en });
export type PathSlug =
  | "inheritance-foundations"
  | "shares-rules"
  | "cases-applications"
  | "special-advanced";
type Station = { title: BilingualText; description: BilingualText };
type RelatedConcept = { title: BilingualText; slug?: string };
export type LearningCurriculum = {
  slug: PathSlug;
  order: number;
  title: BilingualText;
  subtitle: BilingualText;
  heroDescription: BilingualText;
  image: string;
  hoverText: BilingualText;
  outcomes: BilingualText[];
  stations: Station[];
  example: BilingualText;
  relatedConcepts: RelatedConcept[];
  prompts: BilingualText[];
};
const related = {
  owners: {
    title: bi("أصحاب الفروض", "Fixed-share heirs"),
    slug: "fixed-share-heirs",
  },
  share: { title: bi("الفرض", "Fixed share"), slug: "fixed-share" },
  asabah: { title: bi("العصبة", "Residuary heirs"), slug: "asabah" },
  tasib: { title: bi("التعصيب", "Residuary inheritance"), slug: "tasib" },
  blocking: { title: bi("الحجب", "Blocking"), slug: "blocking" },
  awl: { title: bi("العول", "Awl"), slug: "awl" },
  radd: { title: bi("الرد", "Radd"), slug: "radd" },
  heir: { title: bi("الوارث", "Heir") },
  branch: { title: bi("الفرع الوارث", "Heir branch") },
};
const station = (
  ar: string,
  en: string,
  descriptionAr: string,
  descriptionEn: string,
): Station => ({
  title: bi(ar, en),
  description: bi(descriptionAr, descriptionEn),
});

// Static curriculum supplied for the four paths. This is a learning agenda,
// not generated rulings, source quotations, or executable calculation rules.
export const learningPathCurriculum: LearningCurriculum[] = [
  {
    slug: "inheritance-foundations",
    order: 1,
    title: bi("أساسيات الوارث", "Heir Foundations"),
    subtitle: bi(
      "المفاهيم الأساسية: الوارث، التركة، الفروض، العصبات، الحجب، وأهم المصطلحات.",
      "Core concepts: heirs, the estate, fixed shares, residuary heirs, blocking, and essential terminology.",
    ),
    heroDescription: bi(
      "ابدأ من المصطلحات، وابنِ قاعدة واضحة قبل الانتقال إلى الأنصبة والمسائل.",
      "Start with the terminology and build a clear foundation before exploring shares and cases.",
    ),
    image: "/assets/learning-path/beginner.webp",
    hoverText: bi("ابدأ من الأساس", "Start with the basics"),
    outcomes: [
      bi(
        "فهم معنى الوارث والتركة.",
        "Understand the meaning of heir and estate.",
      ),
      bi(
        "التمييز بين أصحاب الفروض والعصبة.",
        "Distinguish fixed-share heirs from residuary heirs.",
      ),
      bi(
        "التعرف على أثر الحجب في الإرث.",
        "Explore the effect of blocking on inheritance.",
      ),
      bi(
        "بناء قاعدة مفاهيمية واضحة قبل الدخول في الأنصبة والمسائل.",
        "Build a clear conceptual foundation before studying shares and cases.",
      ),
    ],
    stations: [
      station(
        "من هو الوارث؟",
        "Who is an heir?",
        "التعرف على من يستحق الإرث من حيث الأصل العام.",
        "Explore the general meaning of entitlement to inherit.",
      ),
      station(
        "ما هي التركة؟",
        "What is the estate?",
        "فهم المقصود بما يخلّفه الميت محلًّا للتوزيع.",
        "Understand what the deceased leaves for distribution.",
      ),
      station(
        "أصحاب الفروض",
        "Fixed-share heirs",
        "مدخل إلى الورثة الذين لهم أنصبة مقدرة.",
        "An introduction to heirs with prescribed shares.",
      ),
      station(
        "العصبة والتعصيب",
        "Residuary heirs and inheritance",
        "فهم من يرث بالباقي وما معنى الإرث بغير تقدير.",
        "Explore receiving the remainder and inheritance without a prescribed share.",
      ),
      station(
        "الحجب",
        "Blocking",
        "كيف يؤثر وجود وارث في إرث وارث آخر.",
        "How the presence of one heir can affect another heir's inheritance.",
      ),
    ],
    example: bi(
      "قبل حساب أي مسألة، نحتاج أولًا إلى معرفة من ذُكر في الحالة، ومن يدخل في الإرث، وهل يوجد من يحجب غيره.",
      "Before calculating a case, identify who is mentioned, who is entitled to inherit, and whether anyone blocks another.",
    ),
    relatedConcepts: [
      related.owners,
      related.share,
      related.asabah,
      related.tasib,
      related.blocking,
    ],
    prompts: [
      bi("ما معنى أصحاب الفروض؟", "Who are fixed-share heirs?"),
      bi("ما معنى العصبة؟", "What are residuary heirs?"),
      bi("ما معنى الحجب؟", "What is blocking?"),
    ],
  },
  {
    slug: "shares-rules",
    order: 2,
    title: bi("الأنصبة والقواعد", "Shares & Rules"),
    subtitle: bi(
      "كيف تتحدد الأنصبة، ومتى تتغير، وكيف تتفاعل القواعد مع اختلاف الورثة.",
      "How shares are determined, when they change, and how rules interact as heirs differ.",
    ),
    heroDescription: bi(
      "اربط بين المصطلح والفكرة، ثم تأمل العلاقة بين الفروض والباقي وأصل المسألة.",
      "Connect each term to its meaning, then explore fixed shares, the remainder, and the case origin.",
    ),
    image: "/assets/learning-path/intermediate.webp",
    hoverText: bi("طبّق ما تعلمت", "Apply what you learned"),
    outcomes: [
      bi(
        "فهم معنى الفرض بوصفه نصيبًا مقدرًا.",
        "Understand a fixed share as a prescribed share.",
      ),
      bi(
        "فهم معنى التعصيب بوصفه إرثًا بغير تقدير.",
        "Understand residuary inheritance as inheritance without a prescribed share.",
      ),
      bi(
        "التعرف على العول والرد بصورة تعليمية مبسطة.",
        "Explore awl and radd through a simple educational introduction.",
      ),
      bi(
        "تكوين صورة أوضح عن منطق الأنصبة في المسألة.",
        "Build a clearer understanding of shares in a case.",
      ),
    ],
    stations: [
      station(
        "الفرض",
        "Fixed share",
        "التعرف على معنى النصيب المقدر في التركة.",
        "Explore the meaning of a prescribed estate share.",
      ),
      station(
        "التعصيب",
        "Residuary inheritance",
        "كيف يعمل الإرث بغير تقدير بعد أصحاب الفروض.",
        "Explore inheritance without a prescribed share after fixed-share heirs.",
      ),
      station(
        "العصبة",
        "Residuary heirs",
        "من هو الوارث الذي يرث بطريق التعصيب.",
        "Explore the heir who inherits by residuary inheritance.",
      ),
      station(
        "العول",
        "Awl",
        "متى تزيد السهام على أصل المسألة.",
        "Explore when shares exceed the case origin.",
      ),
      station(
        "الرد",
        "Radd",
        "متى يبقى جزء من التركة وكيف يُفهم ذلك تعليميًا.",
        "Explore when part of an estate remains and how to understand that educationally.",
      ),
      station(
        "أصل المسألة",
        "Case origin",
        "مدخل مبسط لفهم الأساس الذي تُبنى عليه السهام.",
        "A simple introduction to the basis used for shares.",
      ),
    ],
    example: bi(
      "قد تكون بعض الأنصبة محددة سلفًا، ثم ننظر في الباقي أو في زيادة السهام على الأصل بحسب نوع المسألة.",
      "Some shares may be prescribed; the remainder or shares exceeding the origin are then considered according to the case.",
    ),
    relatedConcepts: [
      related.share,
      related.tasib,
      related.asabah,
      related.awl,
      related.radd,
    ],
    prompts: [
      bi(
        "ما الفرق بين الفرض والتعصيب؟",
        "How do fixed shares and residuary inheritance differ?",
      ),
      bi("لماذا يحدث العول؟", "Why does awl occur?"),
      bi("متى يحصل الرد؟", "When does radd apply?"),
    ],
  },
  {
    slug: "cases-applications",
    order: 3,
    title: bi("المسائل والتطبيقات", "Cases & Applications"),
    subtitle: bi(
      "حالات عملية خطوة بخطوة، من فهم الحالة إلى تحديد الورثة والتوزيع وشرح النتيجة.",
      "Practical cases step by step: understanding the case, identifying heirs, distribution, and explaining the result.",
    ),
    heroDescription: bi(
      "تعرّف على تسلسل قراءة المسألة والتحقق منها، دون إجراء حساب جديد في هذه الصفحة.",
      "Explore the sequence for reading and verifying a case; this page does not perform a new calculation.",
    ),
    image: "/assets/learning-path/advanced.webp",
    hoverText: bi("تعمّق أكثر", "Go deeper"),
    outcomes: [
      bi("قراءة الحالة بصياغتها الطبيعية.", "Read a case in natural language."),
      bi(
        "استخراج الورثة المذكورين في السؤال.",
        "Identify the heirs mentioned in the question.",
      ),
      bi(
        "التمييز بين الحالة الجاهزة وغير الجاهزة.",
        "Distinguish ready cases from those needing more information.",
      ),
      bi(
        "فهم كيف يشرح النظام النتيجة النهائية.",
        "Understand how the system explains the final result.",
      ),
    ],
    stations: [
      station(
        "قراءة الحالة",
        "Read the case",
        "فهم ما الذي يذكره المستخدم في نص المسألة.",
        "Understand what the user states in the case.",
      ),
      station(
        "تحديد الورثة",
        "Identify heirs",
        "استخراج الأشخاص والعلاقات المذكورة في الحالة.",
        "Identify the people and relationships stated in the case.",
      ),
      station(
        "التحقق من اكتمال الحالة",
        "Check completeness",
        "هل المعلومات كافية أم توجد فجوة تحتاج استيضاحًا؟",
        "Is the information sufficient, or does a gap require clarification?",
      ),
      station(
        "التوزيع",
        "Distribution",
        "إذا كانت الحالة مدعومة ومكتملة، يظهر التوزيع المتحقق.",
        "When a case is supported and complete, the verified distribution is shown.",
      ),
      station(
        "شرح النتيجة",
        "Explain the result",
        "يفسر النظام النتيجة اعتمادًا على الأدلة المتاحة.",
        "The system explains the result using available evidence.",
      ),
    ],
    example: bi(
      "توفي رجل وترك زوجة وأم وابنين وبنت. تبدأ العملية بفهم المذكورين، ثم التحقق، ثم عرض التوزيع وشرحه.",
      "A man died leaving a wife, mother, two sons and a daughter. The process starts with understanding those mentioned, then verification, distribution, and explanation.",
    ),
    relatedConcepts: [
      related.heir,
      related.branch,
      related.blocking,
      related.share,
      related.tasib,
    ],
    prompts: [
      bi(
        "كيف نبدأ قراءة مسألة مواريث؟",
        "How do we start reading an inheritance case?",
      ),
      bi("كيف أحدد الورثة في الحالة؟", "How do I identify heirs in a case?"),
      bi(
        "كيف أفهم سبب النتيجة؟",
        "How can I understand the reason for a result?",
      ),
    ],
  },
  {
    slug: "special-advanced",
    order: 4,
    title: bi("الحالات الخاصة والمتقدمة", "Special & Advanced Cases"),
    subtitle: bi(
      "الحالات المركبة أو التي تحتاج معالجة أعمق أو إحالة أو استيضاح.",
      "Complex cases or those requiring deeper analysis, referral, or clarification.",
    ),
    heroDescription: bi(
      "تعلّم قراءة حدود الإجابة، ومتى يكون الاستيضاح أو الرجوع إلى مختص جزءًا من التعامل الموثوق مع المسألة.",
      "Learn to read answer limitations and understand clarification and specialist referral as part of handling a case responsibly.",
    ),
    image: "/assets/learning-path/teachers-students.webp",
    hoverText: bi("استكشف الموارد", "Explore resources"),
    outcomes: [
      bi(
        "فهم الحالات التي لا يكفي فيها السؤال وحده.",
        "Understand cases where the question alone is insufficient.",
      ),
      bi(
        "معرفة متى يجب طلب توضيح إضافي.",
        "Learn when additional clarification is needed.",
      ),
      bi(
        "التمييز بين ما يمكن للنظام دعمه وما يحتاج مختصًا.",
        "Distinguish supported cases from those requiring a specialist.",
      ),
      bi(
        "فهم حدود المنتج بطريقة موثوقة.",
        "Understand the product's limitations.",
      ),
    ],
    stations: [
      station(
        "الاستيضاح",
        "Clarification",
        "متى تكون المعلومات ناقصة أو تحتمل أكثر من تفسير.",
        "When information is incomplete or has multiple interpretations.",
      ),
      station(
        "الإحالة",
        "Referral",
        "متى يكون الرجوع إلى مختص هو الخيار الأنسب.",
        "When consulting a specialist is the appropriate option.",
      ),
      station(
        "الحالات المركبة",
        "Complex cases",
        "حالات تحتاج معالجة أوسع أو أكثر من شرط.",
        "Cases requiring broader handling or multiple conditions.",
      ),
      station(
        "حدود الإصدار",
        "Version limits",
        "ما الذي يغطيه المنتج اليوم، وما الذي لا يزال خارج النطاق.",
        "What the product currently covers and what remains out of scope.",
      ),
    ],
    example: bi(
      "إذا ذُكر أخ دون تحديد نوعه في مسألة مؤثرة، فقد يحتاج النظام إلى استيضاح قبل تقديم جواب نهائي.",
      "If a brother is mentioned without specifying the relationship type where it matters, the system may need clarification before a final answer.",
    ),
    relatedConcepts: [
      related.blocking,
      related.radd,
      related.awl,
      related.branch,
    ],
    prompts: [
      bi(
        "متى تحتاج المسألة إلى استيضاح؟",
        "When does a case need clarification?",
      ),
      bi("متى نُحيل إلى مختص؟", "When is specialist referral needed?"),
      bi("ما الحالات التي تكون خارج النطاق؟", "Which cases are out of scope?"),
    ],
  },
];
