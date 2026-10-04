from unittest.mock import Mock
import pytest
from backend.learning import concept_catalog as catalog
from backend.pipeline import learn_pipeline as learn

IDS = ("fixed_share", "fixed_share_heirs", "residuary_heirs", "blocking", "blocking_deprivation", "blocking_reduction", "awl", "radd", "estate", "heir", "heir_branch", "case_origin")
FIELDS = {"id", "title_ar", "title_en", "definition_ar", "definition_en", "source_title", "source_entry", "reference", "exact_excerpt", "verified"}


def test_empty_evidence_never_invents_content():
    for id in IDS:
        record = catalog.get_curated_concept(id)
        assert FIELDS <= record.keys()
        assert record["verified"] is False
        assert not catalog.is_verified_concept(id)
        assert all(record[field] == "" for field in ("definition_ar", "definition_en", "source_title", "source_entry", "reference", "exact_excerpt"))
    assert catalog.get_curated_concept("unknown") is None


@pytest.mark.parametrize("query,id", [("ما معنى أصحاب الفروض؟", "fixed_share_heirs"), ("ما معنى حجب الحرمان؟", "blocking_deprivation"), ("أَصْل المسألة", "case_origin"), ("What is a fixed share?", "fixed_share"), ("Define estate", "estate"), ("What is a residuary heir?", "residuary_heirs"), ("Blocking by reduction", "blocking_reduction")])
def test_exact_arabic_english_aliases(query, id):
    assert catalog.find_curated_concept_by_query(query)["id"] == id


@pytest.mark.parametrize("query", ["ما الفرق بين العول والرد؟", "مات وترك وارثا", "أصحاب الفروض النسبية", "Explain estate taxes", "How does blocking affect this case?"])
def test_qualifiers_and_cases_do_not_match(query):
    assert catalog.find_curated_concept_by_query(query) is None


def test_existing_verified_definition_and_exact_excerpt(monkeypatch):
    source = {"chunk_id": "neutral", "source_name": "Neutral fixture", "source_url": "https://example.invalid", "verified_source": True, "volume": 1, "page": 2, "section": "Fixture entry"}
    excerpt = "Exact neutral fixture.\n  Whitespace remains unchanged."
    monkeypatch.setattr(catalog, "list_concepts", lambda: [{"concept_id": "fixed_share", "availability": "available", "short_definition": {"ar": "تعريف محايد للاختبار.", "en": "Neutral test definition."}, "sources": [source]}])
    monkeypatch.setattr(catalog, "load_chunks", lambda: [{**source, "text": excerpt}])
    record = catalog.get_curated_concept("fixed_share")
    assert record["verified"] is False
    assert not catalog.is_verified_concept("fixed_share")
    assert record["exact_excerpt"] == excerpt
    assert record["definition_en"] == ""
    assert record["educational_summaries"]["en"]["text"] == "Neutral test definition."
    assert record["educational_summaries"]["en"]["status"] == "draft"
    rag, model = Mock(return_value=[]), Mock()
    monkeypatch.setattr(learn, "retrieve_educational_evidence", rag)
    monkeypatch.setattr(learn.provider, "explain", model)
    assert learn.run_learn("What is a fixed share?")["evidence_status"] == "insufficient"
    rag.assert_called_once()
    model.assert_not_called()
    monkeypatch.setattr(catalog, "load_chunks", lambda: [])
    assert catalog.is_verified_concept("fixed_share") is False


def test_unverified_entry_falls_back_without_guessing(monkeypatch):
    rag = Mock(return_value=[])
    model = Mock()
    monkeypatch.setattr(learn, "retrieve_educational_evidence", rag)
    monkeypatch.setattr(learn.provider, "explain", model)
    result = learn.run_learn("ما معنى التركة؟")
    assert result["decision_state"] == "out_of_scope"
    assert result["evidence_status"] == "insufficient"
    assert result["source_excerpts"] == []
    rag.assert_called_once()
    model.assert_not_called()
