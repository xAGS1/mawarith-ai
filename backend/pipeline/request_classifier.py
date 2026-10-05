"""Small deterministic request-style router; never decides case readiness."""
import re
from typing import Literal
from backend.rules.educational_concepts import matching_text

RequestType = Literal["educational", "calculation"]

_CALCULATION = re.compile(
    r"\b(?:احسب|وزع|قسم التركة|كم نصيب|نصيب كل وارث)\b"
    r"|\b(?:مات|ماتت|توفي|توفيت)\b.{0,80}\b(?:وترك|وتركت|ترك|تركت)\b"
    r"|\b(?:calculate|distribute|divide)\b.*\b(?:estate|inheritance|shares?)\b"
    r"|\b(?:died|deceased)\b.*\b(?:left|leaving|survived)\b", re.I)
_EDUCATIONAL = re.compile(
    r"\b(?:ما معنى|عرف|اشرح|ما الفرق|لماذا|ما المقصود|كيف يعمل|من هم)\b"
    r"|\b(?:what is|what are|explain|difference|compare|why|how does|who are)\b", re.I)
_HEIRS = re.compile(r"\b(?:بنت|ابن|ابنان|ابنين|اخ|اخت|زوجة|ام|اب|brother|sister|daughter|son|wife|mother|father)\b", re.I)
_OUTCOME = re.compile(r"وش يصير|ماذا يحدث|كيف (?:نقسم|توزع)|what happens|how much", re.I)


def classify_request(question: str, advisory=None) -> tuple[RequestType, str]:
    """Explicit phrases win; advice can disambiguate only case-shaped input.

    Defaulting to education avoids treating an arbitrary model label as a
    calculation request. The existing case pipeline alone confirms ambiguity.
    """
    text = matching_text(question.casefold())
    if _CALCULATION.search(text):
        return "calculation", "explicit_calculation"
    if _EDUCATIONAL.search(text):
        return "educational", "explicit_educational"
    if _HEIRS.search(text) and _OUTCOME.search(text):
        return "calculation", "case_outcome"
    case_shaped = _HEIRS.search(text) and re.search(r"\b(?:ترك|فيه|ورثة|heirs|leaving)\b", text)
    if case_shaped and advisory is not None and advisory.intent in {
            "inheritance_case", "mixed_case_and_question"}:
        return "calculation", "advisory_case"
    return "educational", "conservative_default"
