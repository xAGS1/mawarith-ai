"""Terminology-only enrichment; never expands rulings or source text."""
import re

from backend.learning.concept_catalog import _ENTRIES, get_curated_concept
from backend.rules.educational_concepts import matching_text

# Existing educational aliases/source headings; no generated definitions.
_EXTRA = {
    "fixed_share": ("الفروض المقدرة",),
    "residuary_heirs": ("التعصيب", "residuary inheritance"),
}
_SUPPORTED = {"fixed_share_heirs", "fixed_share", "residuary_heirs", "awl",
              "radd", "case_origin", "blocking"}


def _matched_terms(question: str) -> dict:
    """Detect audited aliases using normalization and whole-term matches.

    Longer aliases take precedence so أصحاب الفروض does not also become a
    definition query for الفرض. Matching normalization affects detection only.
    """
    normalized = matching_text(question.casefold())
    candidates = []
    for concept_id, ar, en, aliases in _ENTRIES:
        if concept_id not in _SUPPORTED:
            continue
        terms = (ar, en, *aliases, *_EXTRA.get(concept_id, ()))
        for term in terms:
            match_term = matching_text(term.casefold())
            for match in re.finditer(r"(?<!\w)(?:و)?" + re.escape(match_term) + r"(?!\w)", normalized):
                candidates.append((match.start(), match.end(), concept_id, terms))
    selected, occupied = {}, []
    for start, end, concept_id, terms in sorted(candidates, key=lambda c: -(c[1] - c[0])):
        if any(start < b and end > a for a, b in occupied):
            continue
        occupied.append((start, end))
        selected[concept_id] = terms
    return selected


def expand_embedding_query(question: str) -> str:
    """Append same-language terminology without replacing the original input."""
    selected = _matched_terms(question)
    if not selected:
        return question
    additions = []
    arabic = bool(re.search(r"[\u0621-\u064a]", question))
    for concept_id in sorted(selected):
        # Arabic/English canonical titles plus curated source-heading aliases.
        for term in (*selected[concept_id][:2], *_EXTRA.get(concept_id, ())):
            if bool(re.search(r"[\u0621-\u064a]", term)) == arabic and term not in additions:
                additions.append(term)
    return question + "\n" + " ".join(additions)


def concept_query_filters(question: str, filters: dict | None) -> dict | None:
    """Use existing approved section metadata; never override caller filters.

    If any matched concept lacks verified provenance or sections disagree,
    retain the original unrestricted query. No new payload/index is needed.
    """
    if filters:
        return filters
    selected = _matched_terms(question)
    if not selected:
        return filters
    sections = set()
    for concept_id in selected:
        concept = get_curated_concept(concept_id)
        if not concept or not concept.get("verified") or not concept.get("source", {}).get("section"):
            return filters
        sections.add(concept["source"]["section"])
    return {"section": sections.pop()} if len(sections) == 1 else filters
