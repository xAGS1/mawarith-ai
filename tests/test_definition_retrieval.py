"""Synthetic definition fixtures test routing without inventing source content."""
from unittest.mock import Mock
import hashlib
import pytest
from backend.learning import definition_retrieval as router
from backend.pipeline import learn_pipeline as learn

TERMS = ["العصبة", "أصحاب الفروض", "العول", "الرد", "الوارث", "التركة", "الحجب"]

def record(text, source_id="uqu_mawarith_1"):
    return {"text": text, "source": {"source_id": source_id,
        "source_type": "educational_reference", "source_name": "Synthetic source",
        "verified_source": True, "chunk_id": "synthetic", "char_start": 100,
        "source_url": None, "input_file": "PRIVATE.pdf"}}

@pytest.mark.parametrize("term", TERMS)
def test_direct_uqu_definition_preferred(term, monkeypatch):
    text = term + ": هو مصطلح تجريبي محايد للاختبار."
    monkeypatch.setattr(router, "uqu_candidates", lambda _: [record(text)])
    fallback, trace = Mock(), {}
    result = router.select_definition_evidence("ما معنى " + term, router.definition_intent("ما معنى " + term), fallback, trace)
    assert result[0]["text"] == text
    assert result[0]["provenance"]["excerpt_char_start"] == 100
    assert result[0]["provenance"]["excerpt_sha256"] == hashlib.sha256(text.encode()).hexdigest()
    assert "PRIVATE" not in str(result)
    assert trace["definition_retrieval"]["uqu_sufficient"]
    fallback.assert_not_called()

@pytest.mark.parametrize("term", TERMS)
@pytest.mark.parametrize("uqu_kind", ["empty", "mention", "enumeration", "behavior"])
def test_insufficient_uqu_falls_back(term, uqu_kind, monkeypatch):
    texts = {"mention": "ورد مصطلح " + term + " في عنوان الاختبار.",
             "enumeration": term + ": هم اثنا عشر، فالرجال هم أمثلة الاختبار.",
             "behavior": term + ": هو يأخذ الباقي.", "empty": ""}
    monkeypatch.setattr(router, "uqu_candidates", lambda _: [record(texts[uqu_kind])] if texts[uqu_kind] else [])
    text = term + ": هو مصطلح تجريبي محايد للاختبار."
    fallback = Mock(return_value=[record(text, "kuwaiti_fiqh_encyclopedia")])
    trace = {}
    result = router.select_definition_evidence("ما معنى " + term, router.definition_intent("ما معنى " + term), fallback, trace)
    assert result[0]["source_id"] == "kuwaiti_fiqh_encyclopedia"
    assert trace["definition_retrieval"]["fallback_triggered"]
    fallback.assert_called_once()

def test_neither_source_no_model(monkeypatch):
    monkeypatch.setattr(router, "uqu_candidates", lambda _: [record("العصبة")])
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda _: [record("العصبة: هو يأخذ الباقي.")])
    model = Mock()
    monkeypatch.setattr(learn.provider, "explain", model)
    result = learn.run_learn("ما معنى العصبة؟")
    assert result["evidence_status"] == "insufficient"
    assert result["source_excerpts"] == []
    model.assert_not_called()

def test_selected_evidence_only_and_existing_guard(monkeypatch):
    text = "العصبة: هو مصطلح تجريبي محايد للاختبار."
    monkeypatch.setattr(router, "uqu_candidates", lambda _: [record(text), record("Unrelated material")])
    model = Mock(return_value={"answer": text + " [E1]"})
    monkeypatch.setattr(learn.provider, "explain", model)
    guard = Mock(wraps=learn.guard_claims)
    monkeypatch.setattr(learn, "guard_claims", guard)
    result = learn.run_learn("ما معنى العصبة؟")
    assert result["evidence_status"] == "supported"
    assert result["source_excerpts"][0]["text"] == text
    assert "Unrelated" not in str(model.call_args)
    assert "definition_retrieval" not in result
    guard.assert_called_once()

@pytest.mark.parametrize("text", ["العصبة", "العصبة: هم اثنا عشر.", "العصبة: هو يأخذ الباقي.", "فإن وجد كان له الباقي."])
def test_incomplete_or_behavior_not_definition(text):
    assert router.direct_definition(record(text), router.definition_intent("ما معنى العصبة؟")) is None

def test_non_definition_stays_normal(monkeypatch):
    assert router.definition_intent("لماذا توجد أنصبة محددة؟") is None
    selector = Mock(side_effect=AssertionError("Definition route used"))
    monkeypatch.setattr(learn, "select_definition_evidence", selector)
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda _: [])
    learn.run_learn("لماذا توجد أنصبة محددة؟")
    selector.assert_not_called()
