"""Pinned source integrity without adding or modifying calculation rules."""
import hashlib
import json
from pathlib import Path
import pytest
from backend.learning import concept_catalog as catalog
from backend.learning.comparisons import curated_comparison
from backend.learning.curated import curated_concept
from backend.rag.fiqh.vector_store import load_chunks

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "backend/learning/curated_source_passages.json"
CORPUS = ROOT / "data/fiqh/kuwaiti_encyclopedia/processed/chunks.json"


@pytest.fixture
def approved_corpus(monkeypatch):
    if not CORPUS.exists():
        pytest.skip("Approved local corpus not installed")
    chunks = load_chunks(CORPUS)
    monkeypatch.setattr(catalog, "load_chunks", lambda: chunks)
    return chunks


@pytest.mark.parametrize("concept_id", ["fixed_share_heirs", "blocking", "awl", "radd", "estate", "case_origin"])
def test_exact_pinned_definition_and_provenance(concept_id, approved_corpus):
    entry = json.loads(MANIFEST.read_text(encoding="utf-8"))[concept_id]
    chunk = next(c for c in approved_corpus if c["chunk_id"] == entry["chunk_id"])
    assert chunk["text"][entry["char_start"]:entry["char_end"]] == entry["text"]
    assert hashlib.sha256(entry["text"].encode()).hexdigest() == entry["sha256"]
    assert all(chunk[k] == v for k, v in entry["provenance"].items())
    concept = catalog.get_curated_concept(concept_id)
    assert concept["verified"]
    assert concept["definition"]["status"] == "source_verbatim"
    assert concept["definition_ar"] == concept["exact_excerpt"] == entry["text"]
    assert concept["definition_en"] == ""  # No invented translation/review.
    result = curated_concept(concept["title_ar"], "ar")
    assert result and entry["text"] in result["answer"]
    assert result["source_excerpts"][0]["text"] == entry["text"]


def test_missing_or_changed_source_fails_closed(monkeypatch, approved_corpus):
    monkeypatch.setattr(catalog, "load_chunks", lambda: [])
    assert not catalog.is_verified_concept("fixed_share_heirs")
    changed = [dict(c, text="Changed source") for c in approved_corpus]
    monkeypatch.setattr(catalog, "load_chunks", lambda: changed)
    assert not catalog.is_verified_concept("radd")
    changed = [dict(c, publisher="Unapproved") for c in approved_corpus]
    monkeypatch.setattr(catalog, "load_chunks", lambda: changed)
    assert not catalog.is_verified_concept("estate")


def test_unsupported_entries_remain_empty(approved_corpus):
    for concept_id in ("heir", "heir_branch", "blocking_deprivation", "blocking_reduction"):
        c = catalog.get_curated_concept(concept_id)
        assert not c["verified"] and not c["definition_ar"] and not c["exact_excerpt"]


def test_qualifiers_and_comparison_mapping_preserved(approved_corpus):
    assert "عِنْدَ الْجُمْهُورِ" in catalog.get_curated_concept("estate")["definition_ar"]
    radd = catalog.get_curated_concept("radd")
    assert "النَّسَبِيَّةِ" in radd["definition_ar"]
    assert "عِنْدَ عَدَمِ اسْتِحْقَاقِ الْغَيْرِ" in radd["definition_ar"]
    result = curated_comparison("ما الفرق بين العول والرد؟", "ar")
    assert result and len(result["sources"]) == 2
    for source, excerpt in zip(result["sources"], result["source_excerpts"]):
        c = catalog.get_curated_concept(source["concept_id"])
        assert excerpt["text"] == c["definition_ar"]
        assert excerpt["source_id"] == c["definition"]["source_id"]
