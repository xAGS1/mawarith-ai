"""Small source-bound terminology catalogue, not inheritance distribution rules.

Definitions are supported by the existing approved encyclopedia passages on
العصبة and الفروض المقدرة. They are usable only when those statements are in
the actual retrieved bundle. Matching never modifies returned source text.
"""
import unicodedata


CONCEPTS = (
    {"concept_id": "residuary", "queries": ("residu", "عصبة", "تعصيب"),
     "anchors": ("يستحق كل التركة إذا لم يوجد صاحب فرض", "فإن وجد كان له الباقي", "فإن لم يكن باق فلا شيء له"),
     "ar": {"term": "التعصيب", "explanation": "يرث العاصب ما يبقى بعد إعطاء أصحاب الفروض أنصبتهم. والعاصب الواحد يرث كل التركة إذا لم يوجد صاحب فرض، ولا يأخذ شيئاً إذا لم يبق شيء."},
     "en": {"term": "Residuary inheritance", "explanation": "A residuary heir receives what remains after fixed shares are allocated. A sole residuary heir receives the whole estate when there is no fixed-share heir, and receives nothing if nothing remains."}},
    {"concept_id": "fixed_share", "queries": ("fixed", "الفرض", "الفروض"),
     "anchors": ("الفروض المقدرة", "النصف", "الربع", "الثمن", "الثلثان", "الثلث", "السدس"),
     "ar": {"term": "الفرض", "explanation": "الفرض نصيب مقدّر من التركة، مثل النصف أو الربع أو الثمن."},
     "en": {"term": "Fixed share", "explanation": "A fixed share is a specified fraction of the estate, such as one half, one quarter or one eighth."}},
)


def matching_text(text: str) -> str:
    return " ".join("".join(c for c in unicodedata.normalize("NFD", text)
                            if not unicodedata.combining(c)).split())


def supported_concepts(question: str, language: str, evidence: list[dict]) -> list[dict]:
    query = matching_text(question.lower())
    result = []
    for concept in CONCEPTS:
        if not any(matching_text(term) in query for term in concept["queries"]):
            continue
        for record in evidence:
            text = matching_text(record["text"])
            if all(matching_text(anchor) in text for anchor in concept["anchors"]):
                result.append({"concept_id": concept["concept_id"], **concept[language],
                               "evidence_id": record["evidence_id"]})
                break
    return result


def minimal_answer(concepts: list[dict]) -> str:
    return " ".join(c["explanation"] + " [" + c["evidence_id"] + "]" for c in concepts)
