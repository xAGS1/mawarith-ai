"""Small deterministic definition router; source passages are never rewritten."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
import re

from backend.learning.concept_catalog import get_curated_concept
from backend.rag.fiqh.vector_store import load_chunks
from backend.rules.educational_concepts import matching_text

UQU_DIR = Path(__file__).resolve().parents[2] / "data/fiqh/uqu_mawarith_1/raw"
UQU_METADATA = Path(__file__).resolve().parents[1] / "data/uqu_mawarith_1.metadata.json"
ALIASES = {
    "residuary_heirs": ("العصبة", "التعصيب", "العاصب"),
    "fixed_share_heirs": ("أصحاب الفروض", "أهل الفروض"),
    "awl": ("العول",), "radd": ("الرد",), "heir": ("الوارث",),
    "estate": ("التركة",), "blocking": ("الحجب",),
    "blocking_deprivation": ("حجب الحرمان",), "heir_branch": ("الفرع الوارث",),
    "maternal_siblings": ("أولاد الأم", "الإخوة لأم"),
}
_PUBLIC_KEYS = {"source_id", "source_type", "source_name", "publisher", "institution",
    "section", "topic", "volume", "page", "source_url", "chunk_id", "document_sha256",
    "text_sha256", "chunk_sha256", "excerpt_sha256", "excerpt_char_start", "excerpt_char_end",
    "char_start", "char_end", "verified_source", "offset_basis"}


def definition_intent(question):
    text = matching_text(question).strip(" ؟?.!")
    match = re.fullmatch(r"(?:ما معنى|عرف|ما المقصود\s*بـ?|تعريف)\s*(.+)", text)
    if not match:
        return None
    term = re.sub(r"\s+في (?:المواريث|الميراث)$", "", match[1]).strip()
    concept = next((c for c, aliases in ALIASES.items() if term in
                    {matching_text(a) for a in aliases}), None)
    # Unknown terminology still abstains through this route, never model memory.
    return {"intent": "definition", "canonical_concept": concept, "term": term}


@lru_cache(maxsize=2)
def _pdf_pages(path, modified, expected_hash, metadata_text):
    from backend.rag.uqu_extraction import extract_pages
    metadata = json.loads(metadata_text)
    document = Path(path).read_bytes()
    if hashlib.sha256(document).hexdigest() != expected_hash:
        raise ValueError("UQU source hash mismatch")
    return extract_pages(path, metadata)


def uqu_candidates(term, top_k=5):
    metadata_path = UQU_METADATA
    if not metadata_path.exists():
        return []
    metadata_text = metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    if (metadata.get("source_id") != "uqu_mawarith_1" or
            metadata.get("source_type") != "educational_reference" or
            metadata.get("verified_source") is not True):
        return []
    pdf = UQU_DIR / "mawarith_course-uqu.pdf"
    if not pdf.exists():
        return []
    return rank_candidates(_pdf_pages(str(pdf), pdf.stat().st_mtime_ns,
        metadata["document_sha256"], metadata_text), term, top_k)


def _terms(request):
    return ALIASES.get(request["canonical_concept"], (request["term"],))


def _mentions(text, terms):
    normalized = matching_text(text)
    return any(re.search(r"(?<!\w)[وبل]?" + re.escape(matching_text(t)) + r"(?!\w)", normalized) for t in terms)


def rank_candidates(records, term, top_k=5):
    concept = next((c for c, terms in ALIASES.items() if matching_text(term) in
                    {matching_text(t) for t in terms}), None)
    terms = ALIASES.get(concept, (term,))
    scored = []
    for r in records:
        if r['source'].get('retrieval_eligible') is False:
            continue
        if not _mentions(r["text"], terms):
            continue
        normalized = matching_text(r["text"])
        score = sum(normalized.count(matching_text(t)) for t in terms)
        if re.search(r"اصطلاح|تعريف|المراد|وهو|وهي", normalized):
            score += 10
        scored.append({**r, "score": score})
    return sorted(scored, key=lambda r: -r["score"])[:top_k]


def direct_definition(record, request):
    """Reject mentions, enumerations, incomplete conditions and damaged text."""
    text, source = record["text"], record["source"]
    if source.get("verified_source") is not True:
        return None
    terms = _terms(request)
    paragraphs = list(re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text))
    candidates = [(m.start(), m.end(), None) for m in paragraphs]
    canonical = record.get("canonical_passage")
    if canonical and canonical in text:
        start = text.index(canonical)
        candidates.insert(0, (start, start + len(canonical), None))
    # A terminology sentence may follow a language definition. Preserve the
    # exact sentence and map only an actual nearby source heading, not a guess.
    for m in re.finditer(r"(?m)^\s*اصطلاح[اًا]*:\s*[^\n]+", text):
        preceding = text[:m.start()].splitlines()[-8:]
        heading = next((line.strip() for line in reversed(preceding)
            if len(line.strip().split()) <= 3 and _mentions(line, terms)), None)
        if heading:
            candidates.append((m.start(), m.end(), heading))
    accepted = []
    for start, end, heading in candidates:
        passage = text[start:end]
        normalized = matching_text(passage).strip()
        mapped = (record.get("canonical_concept") == request["canonical_concept"]
                  and request["canonical_concept"] is not None
                  and passage.strip() == record.get("canonical_passage", "").strip())
        if not heading:
            heading = next((line.strip() for line in reversed(text[:start].splitlines()[-8:])
                if len(line.strip().split()) <= 3 and _mentions(line, terms)), None)
        if not (_mentions(passage, terms) or heading or mapped):
            continue
        if not (heading or mapped or any(re.search(
                r"(?<!\w)" + re.escape(matching_text(t)) +
                r"\s*[:،]?\s*(?:في الاصطلاح\s*[:،]?\s*)?(?:هو|هي|وهو|وهي|تعريف|المراد|عبارة عن)\b",
                normalized) for t in terms)):
            continue
        if not re.search(r"\b(?:هو|هي|وهو|وهي|بانه|بانها|تعريف|اصطلاحا|الاصطلاح|المراد)\b", normalized):
            continue
        if len(passage) > 1100 or normalized.endswith(":"):
            continue
        if re.search(r"\b(?:لغة|اللغة)\b", normalized) and "اصطلاح" not in normalized:
            continue
        if re.match(r"^(?:فان|فاذا|اذا|اما|عند|ثانيهما|اولهما)\b", normalized):
            continue
        if re.search(r"(?:هو|هي|وهو|وهي)\s+(?:يرث|ترث|ياخذ|تاخذ|يستحق|تستحق)\b", normalized):
            continue
        if re.search(r"اثنا عشر|عددهم|عدد اصحاب|مثال ذلك|مثلا|فالرِ?جال هم", normalized):
            continue
        if request["canonical_concept"] == "fixed_share_heirs" and re.search(r"النسبية|السببية|اثنا عشر", normalized):
            continue
        if request["canonical_concept"] == "blocking" and re.search(r"حجب (?:بوصف|بشخص|الحرمان|النقصان)", normalized) and not mapped:
            continue
        # Known PDF extraction defects. Do not silently repair source wording.
        if re.search(r"\b(?:ىو|وىو|ىي|وىي|الدورث|التكة|الديراث|كلو|بعضو|منو|عنو|تعريفو)\b|�|\(\s*/\s*\)", normalized):
            continue
        accepted.append((start, end, heading))
    if not accepted:
        return None
    # An approved pinned definition outranks shorter paragraphs describing
    # a subtype elsewhere in the same source chunk.
    start, end, heading = min(accepted, key=lambda x: (
        text[x[0]:x[1]].strip() != (canonical or "").strip(), x[1] - x[0]))
    passage = text[start:end]
    public = {k: v for k, v in source.items() if k in _PUBLIC_KEYS}
    public.update(source_id=source.get("source_id", "kuwaiti_fiqh_encyclopedia"),
        excerpt_char_start=source.get("char_start", 0) + start,
        excerpt_char_end=source.get("char_start", 0) + end,
        excerpt_sha256=hashlib.sha256(passage.encode()).hexdigest())
    if heading:
        public["section"] = heading
    return {"text": passage, "source": public}


def select_definition_evidence(question, request, fiqh_retrieve, trace=None):
    debug = {**request, "uqu_candidates": [], "uqu_sufficient": False,
             "fallback_triggered": False, "kuwaiti_candidates": [], "selected_evidence": []}
    try:
        candidates = uqu_candidates(request["term"])
    except (OSError, ValueError, ImportError) as exc:
        candidates = []
        debug["uqu_error"] = type(exc).__name__
    debug["uqu_candidates"] = [r["source"].get("chunk_id") for r in candidates]
    chosen = next((e for r in candidates if (e := direct_definition(r, request))), None)
    debug["uqu_sufficient"] = chosen is not None
    if chosen is None:
        debug["fallback_triggered"] = True
        candidates = []
        # Reuse approved local catalogue/corpus to find direct definitions that
        # vector retrieval may miss. No religious answer strings are hardcoded.
        concept = get_curated_concept(request["canonical_concept"]) if request["canonical_concept"] else None
        if concept and concept.get("verified"):
            # Keep original full chunk offsets, not offsets relative to a slice.
            source_record = concept["source_records"][concept["definition"]["source_id"]]
            candidates.insert(0, {"text": source_record["exact_text"],
                "source": {k: v for k, v in source_record.items() if k != "exact_text"},
                "canonical_concept": request["canonical_concept"], "canonical_passage": concept["definition_ar"]})
        try:
            local = [{"text": c["text"], "source": {k: v for k, v in c.items() if k != "text"}}
                     for c in load_chunks() if matching_text(c.get("section") or "").strip() in
                     {"ارث", "ميراث", "الميراث", "المواريث"}]
            candidates.extend(rank_candidates(local, request["term"]))
        except (OSError, ValueError):
            pass
        chosen = next((e for r in candidates if (e := direct_definition(r, request))), None)
        if chosen is None:
            try:
                candidates.extend(fiqh_retrieve(question))
            except (RuntimeError, ValueError, OSError):
                debug["fiqh_retrieval_unavailable"] = True
            chosen = next((e for r in candidates if (e := direct_definition(r, request))), None)
        debug["kuwaiti_candidates"] = [r["source"].get("chunk_id") for r in candidates]
    if chosen:
        source = chosen["source"]
        debug["selected_evidence"] = [{"source_id": source["source_id"], "chunk_id": source["chunk_id"]}]
    if trace is not None:
        trace["definition_retrieval"] = debug
    if not chosen:
        return []
    s = chosen["source"]
    return [{"evidence_id": "E1", "text": chosen["text"], "source_name": s["source_name"],
        "source_id": s["source_id"], "source_type": s["source_type"], "section": s.get("section"),
        "reference": {"volume": s.get("volume"), "page": s.get("page")},
        "source_url": s.get("source_url"), "immutable_text": True, "provenance": s}]
