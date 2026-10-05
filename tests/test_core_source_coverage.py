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


@pytest.mark.parametrize("concept_id", ["fixed_share_heirs", "blocking", "awl", "radd", "estate", "case_origin",
                                       "heir", "heir_branch", "blocking_deprivation", "maternal_siblings"])
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
    for concept_id in ("blocking_reduction",):
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


@pytest.mark.parametrize("concept_id", ["heir", "heir_branch", "blocking_deprivation", "maternal_siblings"])
def test_promoted_source_offsets_hashes_and_missing_evidence(concept_id, approved_corpus, monkeypatch):
    c = catalog.get_curated_concept(concept_id)
    source = c["source"]
    chunk = next(x for x in approved_corpus if x["chunk_id"] == source["chunk_id"])
    left = source["excerpt_char_start"] - chunk["char_start"]
    right = source["excerpt_char_end"] - chunk["char_start"]
    assert chunk["text"][left:right] == c["definition_ar"]
    assert source["excerpt_sha256"] == hashlib.sha256(c["definition_ar"].encode()).hexdigest()
    assert source["chunk_sha256"] == hashlib.sha256(chunk["text"].encode()).hexdigest()
    monkeypatch.setattr(catalog, "load_chunks", lambda: [])
    assert not catalog.get_curated_concept(concept_id)["verified"]


def test_new_definitions_do_not_expand_entitlement_or_context(approved_corpus):
    assert catalog.get_curated_concept("heir")["definition_ar"].strip() == "وَثَانِيهَا: الْوَارِثُ وَهُوَ الْحَيُّ بَعْدَ الْمُورَثِ أَوِ الْمُلْحَقُ بِالأَْحْيَاءِ."
    branch = catalog.get_curated_concept("heir_branch")["definition_ar"]
    assert "بِطَرِيقِ الْفَرْضِ أَوِ التَّعْصِيبِ" in branch
    assert "مِنَ الزَّوْجِ أَمْ مِنْ غَيْرِهِ" in branch
    assert "بِنْتُ الْبِنْتِ أَوِ ابْنُ الْبِنْتِ" in branch
    blocking = catalog.get_curated_concept("blocking_deprivation")["definition_ar"]
    assert "إِلاَّ الْمُعْتَقَ" in blocking and "الأَْبَوَانِ وَالزَّوْجَانِ وَالْوَلَدَانِ" in blocking
    maternal = catalog.get_curated_concept("maternal_siblings")
    assert "مِنْ جِهَةِ أُمِّهِ فَقَطْ" in maternal["definition_ar"]
    assert set(maternal["properties"]) == {"definition"}
    assert catalog.find_curated_concept_by_query("ما معنى الإخوة لأم؟")["id"] == "maternal_siblings"


@pytest.mark.parametrize("name,query", [
    ("eligible_origins", "ما أصول المسائل التي تعول؟"),
    ("origin_six_outcomes", "إلى كم يعول أصل المسألة ستة؟"),
    ("origin_24_example", "مثال على العول من 24 إلى 27"),
])
def test_bounded_awl_facts_have_individual_exact_sources(name, query, approved_corpus):
    from backend.learning.knowledge import verified_properties
    c = catalog.get_curated_concept("awl")
    fact = verified_properties(c)[name]
    pin = json.loads(MANIFEST.read_text(encoding="utf-8"))["awl"]["properties"][name]
    assert fact["value"] == pin["text"]
    source = c["source_records"][fact["source_id"]]
    assert source["chunk_id"] == pin["chunk_id"]
    assert source["excerpt_sha256"] == pin["sha256"]
    chunk = next(x for x in approved_corpus if x["chunk_id"] == source["chunk_id"])
    assert chunk["text"][source["excerpt_char_start"] - chunk["char_start"]:
                         source["excerpt_char_end"] - chunk["char_start"]] == fact["value"]
    response = curated_concept(query, "ar")
    assert response["source_excerpts"][0]["text"] == fact["value"]
    assert response["sources"][0]["content_kind"] == "source_verbatim"


def test_changed_awl_property_not_promoted_and_case_not_routed(approved_corpus, monkeypatch):
    from backend.learning.knowledge import verified_properties
    from backend.learning.curated import curated_fact
    pin = json.loads(MANIFEST.read_text(encoding="utf-8"))["awl"]["properties"]["origin_24_example"]
    chunks = [dict(c, text="Changed evidence") if c["chunk_id"] == pin["chunk_id"] else c for c in approved_corpus]
    monkeypatch.setattr(catalog, "load_chunks", lambda: chunks)
    assert "origin_24_example" not in verified_properties(catalog.get_curated_concept("awl"))
    assert curated_fact("مثال على العول من 24 إلى 27", "ar") is None
    assert curated_fact("توفي رجل وترك زوجة وبنتين وأم وأب", "ar") is None
    assert set(catalog.get_curated_concept("radd")["properties"]) == {"definition"}


@pytest.mark.parametrize("question", ["ما معنى الوارث؟", "ما معنى الفرع الوارث؟", "ما معنى حجب الحرمان؟",
                                     "ما معنى أولاد الأم؟", "ما أصول المسائل التي تعول؟",
                                     "إلى كم يعول أصل المسألة ستة؟", "مثال على العول من 24 إلى 27"])
def test_promoted_knowledge_answers_without_llm_or_open_rag(question, approved_corpus, monkeypatch):
    from backend.pipeline import learn_pipeline
    def unexpected(*args, **kwargs):
        pytest.fail("Verified educational source must not use open RAG or LLM")
    monkeypatch.setattr(learn_pipeline, "retrieve_educational_evidence", unexpected)
    from backend.learning.definition_retrieval import definition_intent
    monkeypatch.setattr(learn_pipeline.provider, "explain", (
        lambda q, language, evidence: {"answer": evidence[0]["text"] + " [E1]"}
        ) if definition_intent(question) else unexpected)
    result = learn_pipeline.run_learn(question)
    assert result["evidence_status"] == "supported"
    assert result["mode"] == "learn" and result["case_details"] is None
    assert len(result["source_excerpts"]) == 1
