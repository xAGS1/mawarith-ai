"""Auditable curated concept structure; no model-generated religious content.

Only existing source-bound definitions for fixed_share and residuary_heirs may
be populated, and only while their approved local evidence is available.
All other entries are intentionally empty and unverified.
"""
import re
from backend.learning.catalogs import list_concepts
from backend.rag.fiqh.vector_store import load_chunks
from backend.rules.educational_concepts import matching_text

_ENTRIES = (
    ("fixed_share", "الفرض", "Fixed share", ("الفروض", "fixed shares")),
    ("fixed_share_heirs", "أصحاب الفروض", "Fixed-share heirs", ("صاحب فرض", "fixed-share heir", "fixed share heirs", "fixed share heir")),
    ("residuary_heirs", "العصبة", "Residuary heirs", ("عاصب", "residuary heir")),
    ("blocking", "الحجب", "Blocking", ("حجب",)),
    ("blocking_deprivation", "حجب الحرمان", "Blocking by deprivation", ("deprivation blocking",)),
    ("blocking_reduction", "حجب النقصان", "Blocking by reduction", ("reduction blocking",)),
    ("awl", "العول", "Awl", ("عول",)),
    ("radd", "الرد", "Radd", ("رد",)),
    ("estate", "التركة", "Estate", ("تركة",)),
    ("heir", "الوارث", "Heir", ("وارث", "الورثة", "heirs")),
    ("heir_branch", "الفرع الوارث", "Inheriting descendant", ("فرع وارث", "heir branch")),
    ("case_origin", "أصل المسألة", "Case origin", ("اصل المسالة", "origin of the case")),
)


def get_curated_concept(id: str) -> dict | None:
    entry = next((e for e in _ENTRIES if e[0] == id), None)
    if entry is None:
        return None
    record = {"id": id, "title_ar": entry[1], "title_en": entry[2],
              "definition_ar": "", "definition_en": "", "source_title": "",
              "source_entry": "", "reference": "", "exact_excerpt": "", "verified": False}
    if id not in {"fixed_share", "residuary_heirs"}:
        return record
    card = next((c for c in list_concepts() if c["concept_id"] == id), None)
    if not card or card.get("availability") != "available":
        return record
    definition, sources = card.get("short_definition"), card.get("sources", [])
    if not isinstance(definition, dict) or not all(isinstance(definition.get(lang), str) and definition[lang].strip() for lang in ("ar", "en")):
        return record
    if not sources or not all(s.get("verified_source") is True and s.get("source_name") and s.get("source_url") for s in sources):
        return record
    try:
        chunks = load_chunks()
    except (OSError, ValueError):
        return record
    source = sources[0]
    chunk = next((c for c in chunks if c.get("chunk_id") == source.get("chunk_id")
                  and c.get("verified_source") is True and c.get("source_name") == source["source_name"]
                  and c.get("source_url") == source["source_url"]), None)
    if not chunk or not isinstance(chunk.get("text"), str) or not chunk["text"].strip():
        return record
    record.update(definition_ar=definition["ar"], definition_en=definition["en"],
                  source_title=source["source_name"], source_entry=source.get("section") or "",
                  reference={"volume": source.get("volume"), "page": source.get("page")},
                  exact_excerpt=chunk["text"], verified=True, source=dict(source))
    return record


def find_curated_concept_by_query(text: str) -> dict | None:
    """Exact alias match with a small explicit definition-question wrapper.

    Comparisons, cases, and extra qualifiers do not match a broader concept.
    Unicode normalization affects matching only, never definitions or excerpts.
    """
    query = matching_text(text.casefold()).strip(" ؟?.!")
    query = re.sub(r"^(?:ما معنى|ما هو|ما هي|اشرح مفهوم|اشرح|عرف|what is|what are|what does|define|explain)\s+", "", query)
    query = re.sub(r"^(?:a|an|the)\s+", "", query)
    query = re.sub(r"\s+(?:mean in islamic inheritance|in islamic inheritance|in inheritance|في المواريث|في الميراث|mean)$", "", query)
    for id, ar, en, aliases in _ENTRIES:
        if query in {matching_text(alias.casefold()) for alias in (ar, en, *aliases)}:
            return get_curated_concept(id)
    return None


def is_verified_concept(id: str) -> bool:
    record = get_curated_concept(id)
    return bool(record and record["verified"])
