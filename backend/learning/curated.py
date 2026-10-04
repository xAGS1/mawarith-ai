"""Resolve basic definitions from the existing verified educational catalogue."""
import re
from backend.learning.catalogs import list_concepts
from backend.rules.educational_concepts import matching_text
from backend.learning.concept_catalog import find_curated_concept_by_query


def curated_concept(question: str, language: str) -> dict | None:
    concept = find_curated_concept_by_query(question)
    if concept and concept["verified"]:
        source = concept["source"]
        return {"answer": concept[f"definition_{language}"], "sources": [source],
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
        definition = card.get("short_definition")
        sources = card.get("sources", [])
        if (card.get("availability") == "available" and isinstance(definition, dict)
                and isinstance(definition.get(language), str) and definition[language].strip()
                and sources and all(s.get("verified_source") is True and s.get("source_name")
                                    and s.get("source_url") for s in sources)):
            return {"answer": definition[language], "sources": sources}
    return None
