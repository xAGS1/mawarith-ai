"""Resolve basic definitions from the existing verified educational catalogue."""
import re
from backend.learning.catalogs import list_concepts
from backend.rules.educational_concepts import matching_text
from backend.learning.concept_catalog import find_curated_concept_by_query, get_curated_concept
from backend.learning.knowledge import verified_definition, verified_properties


def curated_fact(question: str, language: str) -> dict | None:
    """Exact bounded educational questions; never route inheritance cases here."""
    queries = {
        "eligible_origins": ("ما أصول المسائل التي تعول؟", "Which case origins may undergo awl?"),
        "origin_six_outcomes": ("إلى كم يعول أصل المسألة ستة؟", "What can origin 6 rise to in awl?"),
        "origin_24_example": ("مثال على العول من 24 إلى 27", "Example of awl from 24 to 27"),
    }
    query = matching_text(question.casefold()).strip(" ؟?.!")
    name = next((name for name, aliases in queries.items() if query in
                 {matching_text(a.casefold()).strip(" ؟?.!") for a in aliases}), None)
    if name is None:
        return None
    concept = get_curated_concept("awl")
    if not concept or not concept.get("verified"):
        return None
    fact = verified_properties(concept).get(name)
    if not fact or fact["status"] != "source_verbatim":
        return None
    source = {k: v for k, v in concept["source_records"][fact["source_id"]].items() if k != "exact_text"}
    source.update(content_kind="source_verbatim", property=name, source_id=fact["source_id"])
    prefix = "نص المصدر الأصلي:\n" if language == "ar" else "Original source passage:\n"
    return {"answer": prefix + fact["value"], "sources": [source],
            "source_excerpts": [{"text": fact["value"], "source_name": source["source_name"],
                "section": source.get("section"), "reference": {"volume": source.get("volume"), "page": source.get("page")},
                "source_url": source["source_url"], "immutable_text": True,
                "content_kind": "source_verbatim", "provenance": source}]}


def curated_concept(question: str, language: str) -> dict | None:
    fact = curated_fact(question, language)
    if fact:
        return fact
    concept = find_curated_concept_by_query(question)
    if concept and concept["verified"] and verified_definition(concept):
        source = concept["source"]
        definition = concept["definition"]
        text = definition["text"]
        if isinstance(text, dict):
            text = text.get(language, "")
        if not text:
            return None
        if definition["status"] == "source_verbatim":
            text = ("نص المصدر الأصلي:\n" if language == "ar" else "Original source passage:\n") + text
        return {"answer": text, "sources": [{**source, "content_kind": definition["status"]}],
                "source_excerpts": [{"text": concept["exact_excerpt"], "source_name": concept["source_title"],
                    "section": concept["source_entry"], "reference": concept["reference"],
                    "source_url": source["source_url"], "immutable_text": True, "provenance": source}]}
    if concept is not None:
        return None
    query = matching_text(question.lower()).strip(" ؟?.!")
    query = re.sub(r"^(?:ما معنى|ما هو|ما هي|اشرح مفهوم|اشرح|عرف|what is|what are|what does|define|explain)\s+", "", query)
    query = re.sub(r"\s+(?:في المواريث|في الميراث|in islamic inheritance|in inheritance|mean in islamic inheritance|mean)$", "", query)
    for card in list_concepts():
        titles = [matching_text(card["title_ar"].lower()), card["title_en"].lower()]
        titles += [title[:-1] for title in titles if title.endswith("heirs")]
        if query not in titles:
            continue
        if card["concept_id"] == "residuary_inheritance":
            return curated_concept("العصبة", language)
        # Legacy summaries without review provenance cannot bypass this schema.
        return None
    return None
