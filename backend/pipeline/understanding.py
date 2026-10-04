"""Advisory understanding with a strict schema and deterministic fallback."""
import re
from contextvars import ContextVar
from typing import Literal
import requests
from pydantic import BaseModel, ConfigDict, Field
from backend.llm import qwen_understanding
from backend.rules.educational_concepts import matching_text

CURRENT_UNDERSTANDING = ContextVar("mawarith_understanding", default=None)
CURRENT_TRACE = ContextVar("mawarith_debug_trace", default=None)


class Understanding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    intent: Literal["learn_concept", "compare_concepts", "inheritance_case", "mixed_case_and_question", "out_of_scope"]
    language: Literal["ar", "en"]
    depth: Literal["simple", "standard", "detailed"] = "standard"
    question_kind: Literal["what", "why", "how", "compare", "calculate"] = "what"
    deceased_gender: Literal["male", "female"] | None = None
    educational_question: str = ""
    ambiguity_candidates: list[str] = Field(default_factory=list, max_length=8)


def fallback_understanding(question: str) -> Understanding:
    text = matching_text(question.casefold())
    language = "ar" if re.search(r"[\u0600-\u06ff]", question) else "en"
    case = bool(re.search(r"مات|توفي|ترك|died|deceased|left behind|survived by", text))
    kind = "what"
    for label, pattern in (("calculate", r"احسب|وزع|calculate|distribut"),
                           ("how", r"كيف|\bhow\b"), ("why", r"لماذا|\bwhy\b"),
                           ("compare", r"الفرق بين|difference between|\bcompare\b")):
        if re.search(pattern, text):
            kind = label
    educational = re.search(r"لماذا.*|كيف.*|\bwhy\b.*|\bhow\b.*", question, re.I)
    intent = ("mixed_case_and_question" if educational else "inheritance_case") if case else (
        "compare_concepts" if kind == "compare" else "learn_concept")
    if not case and not re.search(r"مواريث|ميراث|فرض|عصب|تعصيب|حجب|عول|رد|تركة|وارث|ورثة|نصيب|inherit|heir|share|residu|blocking|awl|radd|estate", text):
        intent = "out_of_scope"
    depth = "detailed" if re.search(r"بالتفصيل|تفصيلي|detailed|in detail", text) else (
        "simple" if re.search(r"ببساطة|مبسط|للمبتدئ|simple|beginner", text) else "standard")
    gender = "male" if re.search(r"توفي رجل|مات رجل|a man died", text) else (
        "female" if re.search(r"توفيت امرأة|ماتت امرأة|a woman died", text) else None)
    ambiguities = ["sibling_type"] if re.search(r"أخ|اخ|brother|sister", question, re.I) else []
    return Understanding(intent=intent, language=language, depth=depth, question_kind=kind,
                         deceased_gender=gender, educational_question=educational.group() if educational else "",
                         ambiguity_candidates=ambiguities)


def understand(question: str) -> tuple[Understanding, str]:
    fallback = fallback_understanding(question)
    if not question.strip():
        return fallback, "deterministic_fallback"
    try:
        result = Understanding.model_validate(qwen_understanding.understand_input(question, Understanding.model_json_schema()))
        if result.educational_question and result.educational_question not in question:
            raise ValueError("Educational question is not an input substring")
        # Explicit case cues and language cannot be overridden by a classifier.
        result.language = fallback.language
        result.deceased_gender = fallback.deceased_gender
        if fallback.intent in {"inheritance_case", "mixed_case_and_question"}:
            result.intent = fallback.intent
            result.educational_question = fallback.educational_question
        return result, "ai"
    except (ValueError, TypeError, KeyError, requests.RequestException):
        return fallback, "deterministic_fallback"
