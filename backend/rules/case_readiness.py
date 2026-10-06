"""Deterministic clarification and v1 capability checks, not new share rules."""
from fractions import Fraction
import re

from backend.rules.case_features import build_case_features
from backend.rules.educational_concepts import matching_text


def assess_case(question: str, parsed: dict, rules: list[dict]) -> dict:
    text = matching_text(question.lower())
    arabic = bool(re.search(r"[\u0600-\u06ff]", question))

    def decision(state, reason, ar=None, en=None):
        return {"decision_state": state, "reason": reason,
                "clarification_question": (ar if arabic else en) if state == "needs_clarification" else None}

    if not text:
        return decision("needs_clarification", "missing_case", "من توفي، ومن الأقارب المذكورين في المسألة؟",
                        "Who died, and which relatives are mentioned in the case?")
    for match in re.finditer(r"\b(?:و|ف)?(?:اخ|اخا|اخوان|اخوين|اخوة|اخت|اختا|اختان|اختين|اخوات)\b", text):
        if not re.match(r"\s+(?:شقيق\w*|اشقاء|لاب|لام|من\s+(?:جهة\s+)?(?:الاب|الام))", text[match.end():]):
            return decision("needs_clarification", "ambiguous_sibling",
                "هل الأخ أو الأخت شقيق، أم لأب، أم لأم؟",
                "Is the brother or sister a full sibling, a paternal half-sibling, or a maternal half-sibling?")
    for match in re.finditer(r"\b(?:brothers?|sisters?|siblings?)\b", text):
        before, after = text[max(0, match.start() - 25):match.start()], text[match.end():match.end() + 35]
        if not (re.search(r"\b(?:full|paternal|maternal)(?:\s+half[- ]?)?\s*$", before)
                or re.match(r"\s+(?:is\s+)?(?:full|paternal|maternal)\b|\s+(?:on|from)\s+(?:the\s+)?(?:father's|mother's)", after)):
            return decision("needs_clarification", "ambiguous_sibling",
                "هل الأخ أو الأخت شقيق، أم لأب، أم لأم؟",
                "Is the brother or sister a full sibling, a paternal half-sibling, or a maternal half-sibling?")
    relations = {r["relation"] for r in parsed.get("mentioned_relatives", []) if r.get("count", 0) > 0}
    if relations.intersection({"أخ", "أخت"}):
        return decision("needs_clarification", "ambiguous_sibling",
            "هل الأخ أو الأخت شقيق، أم لأب، أم لأم؟",
            "Is the brother or sister a full sibling, a paternal half-sibling, or a maternal half-sibling?")
    if relations.intersection({"جد", "جدة"}):
        return decision("needs_clarification", "ambiguous_grandparent",
            "ما صلة الجد أو الجدة بالتحديد: من جهة الأب أم الأم، وما سلسلة القرابة؟",
            "What is the grandparent's exact relationship: through the father or mother, and through which relatives?")
    if re.search(r"ورثة اخرون|اقارب اخرون|other heirs|other relatives", text):
        return decision("needs_clarification", "unlisted_relatives",
            "من بقية الأقارب المذكورين، وما صلة كل منهم وعددهم؟",
            "Who are the other relatives, and what are their exact relationships and counts?")
    uncertainty = r"(?:غير معروف|غير معلوم|لا اعرف|لا ادري|لا نعلم|unknown|unspecified|not sure)"
    family = r"(?:عدد|ابناء|اولاد|اطفال|اخوة|اب|ام|زوج|ابن|بنت|number|children|parents|father|mother|wife|husband|son|daughter)"
    if (re.search(uncertainty + r".{0,40}" + family + "|" + family + r".{0,40}" + uncertainty, text)
            and not re.search(uncertainty + r".{0,20}(?:نصيب|حصة|share)", text)):
        return decision("needs_clarification", "uncertain_family_information",
            "يرجى توضيح المعلومة غير المعروفة: الأقارب الموجودون وصلة كل منهم وعددهم.",
            "Please clarify the unknown family information: which relatives survive, their exact relationships and their counts.")
    if (re.search(r"\b(?:و|ف)?(?:اطفالا?|اولادا?|children)\b", text)
            and not re.search(r"ابن|بنت|ابناء|بنات|بنين|sons?\b|daughters?\b", text)):
        return decision("needs_clarification", "unspecified_children",
            "كم عدد الأبناء وكم عدد البنات؟", "How many sons and how many daughters are there?")
    if re.search(r"حامل|حمل|جنين|مفقود|مناسخ|وصية|وصايا|اختلاف الدين|قتل|طلاق|pregnan|unborn|missing person|successive deaths|last will|a will|the will|bequest|divorc", text):
        return decision("specialist_referral", "advanced_case")
    if not relations:
        if re.search(r"مات|توفي|ترك|ميراث|مواريث|ورثة|inherit|estate|died", text):
            return decision("needs_clarification", "missing_relatives",
                "من الأقارب الذين تركهم المتوفى، وما عدد كل منهم؟",
                "Which relatives did the deceased leave, and how many of each?")
        return decision("out_of_scope", "not_an_inheritance_case")
    features = build_case_features(parsed)
    from backend.rules.safety import unsupported_case_reason
    unsupported = unsupported_case_reason(parsed)
    if unsupported:
        return decision("specialist_referral", unsupported)
    if features["has_father"] and features["has_daughter"] and not features["has_son"]:
        return decision("specialist_referral", "father_residue_not_covered")
    if rules:
        total = sum((Fraction(r["result"]["fraction"]) for r in rules if "fraction" in r["result"]), Fraction())
        has_residue = any(r["result"].get("allocation") == "residue" for r in rules)
        if total > 1 or (not has_residue and total != 1):
            return decision("specialist_referral", "complete_distribution_not_covered")
    return decision("ready", "ready_for_coverage_check")
