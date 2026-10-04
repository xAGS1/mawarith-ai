import type { AskMode } from "./types";

/** Deliberately conservative routing hint; the backend owns all case decisions. */
export function inferMode(question: string): AskMode {
  const text = question.trim().toLowerCase();
  if (
    /(?:مات|ماتت|توفي|توفيت|توفى|المتوفى|المتوفاة|ترك|تركت)\s+(?:وترك|وتركت|زوج|زوجة|ابن|ابنين|بنت|أم|أب|أخ|أخت|ورثة)|(?:مات|توفي|توفى).*(?:ترك|ورثة)|\b(?:died|deceased|passed away)\b.*\b(?:leaving|left|heirs|wife|husband|sons?|daughters?|mother|father|brother|sister)\b|\bleft (?:behind )?(?:a |an |his |her )?(?:wife|husband|son|daughter|mother|father|heirs)\b/u.test(
      text,
    )
  )
    return "case";
  // Explicit conceptual questions stay educational even when they mention shares.
  if (
    /^(?:ما (?:معنى|هو|هي|الفرق)|اشرح|عرّف|عرف|what (?:is|are|does)|explain|define)\b/u.test(
      text,
    ) ||
    /^(?:ما معنى|ما هو|ما هي|ما الفرق|اشرح|عرّف|عرف)/u.test(text)
  )
    return "learn";
  if (
    /(?:احسب|حساب نصيب|وزع|وزّع|قسّم|قسم التركة|توزيع التركة|نصيب كل وريث)|\b(?:calculate|compute|distribute|divide)\b.*\b(?:inheritance|estate|shares|heirs)\b/u.test(
      text,
    )
  )
    return "case";
  return "learn";
}
