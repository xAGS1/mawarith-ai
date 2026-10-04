"""Exact, deterministic comparisons of the two source-bound v1 concepts."""
import re

from backend.learning.concept_catalog import get_curated_concept
from backend.rules.educational_concepts import CONCEPTS, matching_text

_ALIASES = {
    "الفرض": "fixed_share", "الفروض": "fixed_share",
    "fixed share": "fixed_share", "fixed shares": "fixed_share",
    "التعصيب": "residuary_heirs", "العصبة": "residuary_heirs",
    "residuary inheritance": "residuary_heirs", "residuary heirs": "residuary_heirs",
}


def curated_comparison(question: str, language: str) -> dict | None:
    # Full matches deliberately exclude cases, qualifiers and additional concepts.
    query = matching_text(question.casefold()).strip(" ؟?.!")
    match = re.fullmatch(r"ما الفرق بين (.+?) و\s*(.+)", query)
    if match is None:
        match = re.fullmatch(r"what is the difference between (.+?) and (.+)", query)
    if match is None:
        return None
    ids = [_ALIASES.get(term.strip()) for term in match.groups()]
    if set(ids) != {"fixed_share", "residuary_heirs"}:
        return None
    concepts = [get_curated_concept(id) for id in ids]
    if any(not c or c.get("verified") is not True
           or not c.get(f"definition_{language}") or not c.get("exact_excerpt")
           or not c.get("source") for c in concepts):
        return None
    answer, sources, excerpts = [], [], []
    for index, concept in enumerate(concepts, 1):
        evidence_id = f"E{index}"
        source = {**concept["source"], "concept_id": concept["id"], "evidence_id": evidence_id}
        text = concept["exact_excerpt"]
        # Prefer a complete supporting paragraph; never shorten away a condition.
        metadata = next(c for c in CONCEPTS if c["concept_id"] ==
                        ("residuary" if concept["id"] == "residuary_heirs" else "fixed_share"))
        paragraphs = re.findall(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text)
        supported = [p for p in paragraphs if all(matching_text(a) in matching_text(p)
                                                for a in metadata["anchors"])]
        if supported:
            text = min(supported, key=len)
        answer.append(concept[f"definition_{language}"] + f" [{evidence_id}]")
        sources.append(source)
        excerpts.append({"text": text, "concept_id": concept["id"], "evidence_id": evidence_id,
                         "source_name": concept["source_title"], "section": concept["source_entry"],
                         "reference": concept["reference"], "source_url": source.get("source_url"),
                         "immutable_text": True, "provenance": source})
    return {"answer": "\n\n".join(answer), "sources": sources, "source_excerpts": excerpts}
