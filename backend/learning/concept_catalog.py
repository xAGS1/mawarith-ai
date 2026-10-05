"""Auditable curated concept structure; no model-generated religious content.

Definitions are populated only while their pinned approved local evidence is
available. Unsupported entries remain empty and unverified.
"""
import re
import json
import hashlib
from pathlib import Path
from backend.learning.catalogs import list_concepts
from backend.rag.fiqh.vector_store import load_chunks
from backend.rules.educational_concepts import matching_text
from backend.rules.educational_concepts import CONCEPTS
from backend.learning.knowledge import verified_definition


def _exact_match(text: str, needle: str) -> str | None:
    """Match diacritics-insensitively but return an untouched original slice."""
    import unicodedata
    normalized, positions = [], []
    for index, char in enumerate(text):
        for decomposed in unicodedata.normalize("NFD", char):
            if not unicodedata.combining(decomposed):
                normalized.append(decomposed)
                positions.append(index)
    match = re.search(re.escape(matching_text(needle)).replace(r"\ ", r"\s+"), "".join(normalized))
    if not match:
        return None
    end = positions[match.end() - 1] + 1
    while end < len(text) and unicodedata.combining(text[end]):
        end += 1
    return text[positions[match.start()]:end]


def _migrate_content(record: dict, definition: dict, text: str, source: dict):
    source_id = source["chunk_id"]
    record["source_records"] = {source_id: {**source, "exact_text": text}}
    metadata = CONCEPTS[1] if record["id"] == "fixed_share" else CONCEPTS[0]
    paragraphs = re.findall(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text)
    supporting = [p for p in paragraphs if all(matching_text(a) in matching_text(p) for a in metadata["anchors"])]
    # No review identity/date is fabricated during migration.
    record["educational_summaries"] = {lang: {"text": value, "status": "draft", "source_id": source_id,
        "reviewer": None, "reviewed_at": None} for lang, value in definition.items()}
    if not supporting:
        return
    passage = min(supporting, key=len)

    def verbatim(value):
        return {"value": value, "status": "source_verbatim", "source_id": source_id,
                "reviewer": None, "reviewed_at": None}

    record["definition"] = {"text": passage, "status": "source_verbatim", "source_id": source_id,
                            "reviewer": None, "reviewed_at": None}
    properties = {"share_type": verbatim(passage)}
    if record["id"] == "fixed_share":
        properties["has_fixed_fraction"] = verbatim(passage)
        fractions = [_exact_match(passage, token) for token in metadata["anchors"][1:]]
        if all(fractions):
            properties["examples_of_fraction"] = verbatim(fractions)
    else:
        for name, anchor in zip(("may_receive_whole_estate", "may_receive_remainder", "may_receive_nothing"), metadata["anchors"]):
            exact = _exact_match(passage, anchor)
            if exact:
                # Keep the antecedent and all outcomes together: "if found"
                # must never lose its reference to the fixed-share heir.
                properties[name] = verbatim(passage)
    record["properties"] = properties
    record["verified"] = verified_definition(record)
    # Compatibility fields never promote draft summaries into verified content.
    record["definition_ar"] = passage

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
    record.update(definition={"text": "", "status": "draft", "source_id": None,
                              "reviewer": None, "reviewed_at": None},
                  properties={}, source_records={}, educational_summaries={})
    if id not in {"fixed_share", "residuary_heirs"}:
        _load_pinned_definition(record)
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
    record.update(source_title=source["source_name"], source_entry=source.get("section") or "",
                  reference={"volume": source.get("volume"), "page": source.get("page")},
                  exact_excerpt=chunk["text"], source=dict(source))
    _migrate_content(record, definition, chunk["text"], source)
    return record


def _load_pinned_definition(record: dict) -> None:
    """Fail closed on changed/missing corpus, provenance, or exact passage."""
    try:
        entries = json.loads(Path(__file__).with_name("curated_source_passages.json").read_text(encoding="utf-8"))
        selected = entries.get(record["id"])
        if not selected:
            return
        chunk = next((c for c in load_chunks() if c["chunk_id"] == selected["chunk_id"]), None)
        if not chunk or chunk.get("verified_source") is not True:
            return
        if any(chunk.get(k) != v for k, v in selected["provenance"].items()):
            return
        passage = selected["text"]
        start, end = selected["char_start"], selected["char_end"]
        if chunk["text"][start:end] != passage or hashlib.sha256(passage.encode()).hexdigest() != selected["sha256"]:
            return
    except (OSError, ValueError, KeyError, TypeError):
        return
    source = {k: v for k, v in chunk.items() if k != "text"}
    source.update(excerpt_char_start=chunk["char_start"] + start,
                  excerpt_char_end=chunk["char_start"] + end)
    item = {"status": "source_verbatim", "source_id": chunk["chunk_id"],
            "reviewer": None, "reviewed_at": None}
    record.update(definition={"text": passage, **item}, definition_ar=passage,
                  exact_excerpt=passage, source=source, source_title=source["source_name"],
                  source_entry=source.get("section") or "",
                  reference={"volume": source.get("volume"), "page": source.get("page")},
                  source_records={chunk["chunk_id"]: {**source, "exact_text": chunk["text"]}},
                  properties={"definition": {"value": passage, **item}})
    record["verified"] = verified_definition(record)


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
    return bool(record and record["verified"] and verified_definition(record))
