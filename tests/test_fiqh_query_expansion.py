import pytest
from backend.rag.fiqh.query_expansion import expand_embedding_query


@pytest.mark.parametrize("question,term", [
    ("ما معنى أصحاب الفروض؟", "أصحاب الفروض"),
    ("ما معنى الفرض؟", "الفروض المقدرة"),
    ("ما الفروض المقدرة الستة؟", "الفروض المقدرة"),
    ("ما معنى العَصَبَة؟", "العصبة"),
    ("اشرح التعصيب", "العصبة"),
    ("ما معنى العول؟", "العول"),
    ("ما معنى الرد؟", "الرد"),
    ("ما معنى أصل المسألة؟", "أصل المسألة"),
    ("ما معنى الحجب؟", "الحجب"),
    ("What is residuary inheritance?", "Residuary heirs"),
])
def test_deterministic_terminology_preserves_original(question, term):
    result = expand_embedding_query(question)
    assert result.startswith(question + "\n")
    assert term in result
    assert result == expand_embedding_query(question)


def test_both_comparison_terms_and_no_broader_overlap():
    result = expand_embedding_query("ما الفرق بين الفرض والتعصيب؟")
    suffix = result.split("\n")[1]
    assert "الفروض المقدرة" in suffix and "العصبة" in suffix
    suffix = expand_embedding_query("أصحاب الفروض").split("\n")[1]
    assert "الفروض المقدرة" not in suffix


@pytest.mark.parametrize("question", ["توفي رجل وترك بنتًا وأخًا.", "رددت الكتاب", "الردود", "فرضية", "What is friendship?"])
def test_non_concept_questions_and_partial_words_unchanged(question):
    assert expand_embedding_query(question) == question


def test_filter_requires_verified_consistent_provenance_and_respects_caller(monkeypatch):
    from backend.rag.fiqh import query_expansion as module
    monkeypatch.setattr(module, "get_curated_concept", lambda _: {"verified": True, "source": {"section": "Inheritance"}})
    assert module.concept_query_filters("الحجب", None) == {"section": "Inheritance"}
    assert module.concept_query_filters("ما الفرق بين الفرض والتعصيب؟", None) == {"section": "Inheritance"}
    explicit = {"volume": 3}
    assert module.concept_query_filters("الحجب", explicit) is explicit
    monkeypatch.setattr(module, "get_curated_concept", lambda _: {"verified": False})
    assert module.concept_query_filters("الحجب", None) is None
    assert module.concept_query_filters("توفي رجل وترك بنتًا وأخًا.", None) is None
    monkeypatch.setattr(module, "get_curated_concept", lambda cid: {"verified": True, "source": {"section": cid}})
    assert module.concept_query_filters("ما الفرق بين الفرض والتعصيب؟", None) is None
