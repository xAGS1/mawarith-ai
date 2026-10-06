"""Approved-source semantic retrieval without concept or definition gates."""
from functools import lru_cache
import hashlib
import json
import re
import os
from pathlib import Path
from backend.learning import definition_retrieval as uqu
from backend.rag.fiqh.embeddings import embed_texts, embedding_model_name
from backend.rag.fiqh.retriever import retrieve_fiqh
from backend.sources.quran.quranenc import get_quran_verse
from backend.rag.dorar_retrieval import dorar_candidates, ranking_score
from backend.rag.source_mode import cloud_sources, cloud_candidates


def uqu_records():
    pdf = uqu.UQU_DIR / "mawarith_course-uqu.pdf"
    if not pdf.exists() or not uqu.UQU_METADATA.exists():
        return []
    metadata_text = uqu.UQU_METADATA.read_text(encoding="utf-8")
    metadata = json.loads(metadata_text)
    if metadata.get("verified_source") is not True:
        return []
    pages = uqu._pdf_pages(str(pdf), pdf.stat().st_mtime_ns, metadata["document_sha256"], metadata_text)
    return source_windows(pages)


def source_windows(pages):
    records = []
    for page in pages:
        if page['source'].get('retrieval_eligible') is False:
            continue
        text = page["text"]
        start = 0
        while start < len(text):
            end = min(start + 1400, len(text))
            if end < len(text):
                boundary = text.rfind("\n", start + 700, end)
                if boundary > start:
                    end = boundary + 1
            excerpt = text[start:end]
            if excerpt.strip():
                records.append({"text": excerpt, "source": {**page["source"],
                    "char_start": page["source"].get("char_start", 0) + start,
                    "char_end": page["source"].get("char_start", 0) + end,
                    "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest()}})
            if end == len(text):
                break
            # Overlap maintains nearby conditions and headings; source unchanged.
            start = max(start + 1, text.rfind("\n", start, max(start + 1, end - 180)) + 1)
    return records


def quran_records():
    """Select only locally cached approved verses, resolved by the exact adapter."""
    root = Path(__file__).resolve().parents[2] / "data/sources/quran_cache"
    records = []
    for path in sorted(root.glob("*.json")):
        if not re.fullmatch(r"\d+_\d+", path.stem):
            continue
        surah, ayah = map(int, path.stem.split("_"))
        verse = get_quran_verse(surah, ayah)
        if verse.get("immutable_text") is True and verse.get("arabic_text"):
            records.append({"text": verse["arabic_text"], "source": {**verse,
                "source_id": f"quran:{surah}:{ayah}", "source_type": "quran",
                "source_name": "القرآن الكريم", "reference": f"{surah}:{ayah}"}})
    return records


@lru_cache(maxsize=4)
def _vectors(texts, model):
    return embed_texts(list(texts))


def semantic_candidates(query, records, top_k):
    if not records:
        return []
    vectors = _vectors(tuple(r["text"] for r in records), embedding_model_name())
    query_vector = embed_texts([query])[0]
    scored = [{**r, "score": sum(a*b for a, b in zip(query_vector, v))} for r, v in zip(records, vectors)]
    return sorted(scored, key=lambda r: -r["score"])[:top_k]


def retrieve_context(question, request, trace=None):
    query = "\n".join([question, request.retrieval_query, *request.concepts]).strip()
    candidates, failures = [], []
    def fiqh_candidates():
        # General inheritance-domain metadata, not a concept/phrase router.
        from backend.pipeline.learn_pipeline import inheritance_section_filter
        hits = retrieve_fiqh(query, top_k=3, filters=inheritance_section_filter(), semantic_only=True)
        return semantic_candidates(query, source_windows(hits), 3)

    providers = [
        ("uqu", lambda: semantic_candidates(query, uqu_records(), 2)),
        ("fiqh", fiqh_candidates),
        ("dorar", lambda: dorar_candidates(question, query, 3)),
        ("quran", lambda: semantic_candidates(query, quran_records(), 1)),
    ]
    if cloud_sources():
        providers = [
            ("uqu", lambda: cloud_candidates(query, "mawarith_uqu", 2, source_id="uqu_mawarith_1")),
            ("fiqh", fiqh_candidates),
            ("dorar", lambda: dorar_candidates(question, query, 3)),
            ("quran", lambda: cloud_candidates(query, os.getenv("FIQH_COLLECTION", "mawarith_fiqh"), 1, source_type="quran")),
        ]
    for name, retrieve in providers:
        try:
            candidates.extend(retrieve())
        except (RuntimeError, OSError, ValueError) as exc:
            failures.append({"source": name, "error_type": type(exc).__name__})
    # Soft educational preference, never a source sufficiency gate.
    candidates.sort(key=lambda r: -ranking_score(question, r))
    evidence, seen, remaining = [], set(), 7500
    for r in candidates:
        text, source = r["text"], r["source"]
        if text in seen or not text.strip() or len(text) > remaining or r.get("score", 0) < 0.3:
            continue
        seen.add(text)
        public = {k: v for k, v in source.items() if k in {
            "source_id", "source_name", "source_type", "institution", "publisher", "reference",
            "section", "topic", "page", "volume", "source_url", "book", "chapter", "subsection",
            "canonical_url", "content_kind", "page_title"}}
        evidence.append({"evidence_id": f"E{len(evidence)+1}", "text": text,
            "source_name": source["source_name"], "source_type": source.get("source_type"),
            "section": source.get("section") or source.get("topic"), "page": source.get("page"),
            "source_url": source.get("source_url"), "reference": source.get("reference"),
            "immutable_text": True, "provenance": public, "internal_provenance": source})
        remaining -= len(text)
    if trace is not None:
        trace.update(retrieval_query=query, retrieval_failures=failures,
            selected_evidence=[{"evidence_id": e["evidence_id"], "provenance": e["internal_provenance"]} for e in evidence])
    return evidence
