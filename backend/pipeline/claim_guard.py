"""Conservative explanation filtering, never an allocation or readiness engine.

An evidence ID, heir mention or fraction match alone does not prove a claim.
Keep exact complete supporting statements, existing source-bound definitions,
or a narrowly recognized entitlement sentence backed by a confirmed rule.
Unrecognized sensitive paraphrases fail closed. This is not a semantic verifier.
"""
import re
from fractions import Fraction
from backend.rules.educational_concepts import matching_text

GENERAL_AR = "الأدلة الحالية غير كافية لتحديد هذا الحكم."
HEIR_AR = "الأدلة الحالية لا تكفي لتحديد نصيب هذا الوارث."
_SENSITIVE = re.compile(
    r"\b(?:يرث|ترث|يستحق|تستحق|يحجب|محجوب\w*|يحرم|تحرم|يحصل|تحصل|ياخذ|تاخذ|"
    r"نصيب\w*|انصبة|(?:ال)?(?:نصف|ربع|ثمن|ثلث\w*|سدس)|الباقي|عصبة|العصبة|التعصيب|"
    r"(?:ال)?(?:عول|رد)|محروم\w*|حجب|ارث|حصة|يمنح|يشترط|شروط|توزيع|يتقاسم\w*|inherit\w*|entitl\w*|receiv\w*|exclud\w*|block\w*|"
    r"shares?|fractions?|remainder|residu\w*|awl|radd|distribut\w*|eligible|takes?|gets?)\b|\d+\s*/\s*\d+|\d+\s*%", re.I)
_HEIR = re.compile(r"\b(?:ال)?(?:اخ\w*|اخت\w*|زوج\w*|ام|اب|ابن\w*|بنت\w*|بنات|ابناء|"
                   r"brothers?|sisters?|wife|mother|father|sons?|daughters?|heirs?)\b", re.I)
_FRACTIONS = {"النصف": "1/2", "الربع": "1/4", "الثمن": "1/8", "الثلث": "1/3",
              "السدس": "1/6", "الثلثان": "2/3"}


def _units(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?؟])\s+(?!\[)|\n+", text) if part.strip()]


def _clean(text: str) -> str:
    text = re.sub(r"\[(?:E\d+|\d+)\]", "", text)
    return matching_text(text.casefold()).strip(" .،,:;؛!?؟-* ")


def _simple_entitlement(sentence: str, rules: list[dict]) -> bool:
    # Only this bounded sentence form may omit a confirmed case condition.
    match = re.fullmatch(r"(?:ال)?(زوجة|ام|ابن|بنت|اخ|اخت)\s+(?:تاخذ|ياخذ|يحصل على|تحصل على)\s+"
                         r"(النصف|الربع|الثمن|الثلثان|الثلث|السدس|\d+/\d+)"
                         r"(?:\s+من\s+(?:الميراث|التركة))?", sentence)
    if not match:
        return False
    heir, fraction = match.groups()
    fraction = _FRACTIONS.get(fraction, fraction)
    for rule in rules:
        if not rule.get("rule_id") or not rule.get("source", {}).get("reference"):
            continue
        relations = {_clean(r) for r in rule.get("applies_to", [])}
        expected = rule.get("result", {}).get("fraction")
        if heir in relations and expected:
            try:
                if Fraction(fraction) == Fraction(expected):
                    return True
            except (ValueError, ZeroDivisionError):
                pass
    return False


def guard_claims(answer: str, evidence: list[dict] = (), confirmed_rules: list[dict] = (),
                 supported_definitions: list[dict] = (), language: str = "ar") -> dict:
    kept, blocked, supported = [], [], 0
    for sentence in _units(answer):
        cleaned = _clean(sentence)
        conditional = bool(_HEIR.search(cleaned) and re.search(r"\b(?:اذا|عند|بشرط|if|when|unless)\b", cleaned))
        if not _SENSITIVE.search(cleaned) and not conditional:
            kept.append(sentence)
            continue
        ids = set(re.findall(r"\[(E\d+)\]", sentence))
        scoped = [e for e in evidence if not ids or e.get("evidence_id") in ids]
        exact = {_clean(unit) for e in scoped for unit in _units(e.get("text", ""))}
        exact.update(_clean(unit) for rule in confirmed_rules for unit in _units(rule.get("rule", "")))
        exact.update(_clean(unit) for definition in supported_definitions
                     if definition.get("evidence_id") and definition["evidence_id"] in {e.get("evidence_id") for e in scoped}
                     for unit in _units(definition.get("explanation", "")))
        if cleaned in exact or _simple_entitlement(cleaned, confirmed_rules):
            kept.append(sentence)
            supported += 1
        else:
            heir = bool(_HEIR.search(cleaned))
            fallback = (HEIR_AR if heir else GENERAL_AR) if language == "ar" else (
                "The current evidence is insufficient to determine this heir's share." if heir else
                "The current evidence is insufficient to determine this ruling.")
            if fallback not in kept:
                kept.append(fallback)
            blocked.append(sentence)
    if not kept:
        kept = [GENERAL_AR if language == "ar" else "The current evidence is insufficient to determine this ruling."]
    return {"answer": "\n".join(kept) if blocked or not answer.strip() else answer,
            "blocked_claims": blocked, "supported_sensitive_claims": supported}
