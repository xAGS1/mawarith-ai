from unittest.mock import Mock
from backend.learning import curated
from backend.pipeline import learn_pipeline as learn
from backend.pipeline.educational_grounding import relevant_public_excerpts


def test_fixed_share_heirs_uses_verified_catalogue_without_rag_or_model(monkeypatch):
    source = {"source_name": "Neutral catalogue fixture", "source_url": "https://example.invalid", "verified_source": True}
    monkeypatch.setattr(curated, "list_concepts", lambda: [{"title_ar": "أصحاب الفروض", "title_en": "Fixed-share heirs", "availability": "available", "short_definition": {"ar": "تعريف محايد مخصص للاختبار.", "en": "Neutral curated fixture definition."}, "sources": [source]}])
    retrieve, model = Mock(), Mock()
    monkeypatch.setattr(learn, "retrieve_educational_evidence", retrieve)
    monkeypatch.setattr(learn.provider, "explain", model)
    out = learn.run_learn("ما معنى أصحاب الفروض؟")
    assert out["decision_state"] == "ready"
    assert out["answer"] == "تعريف محايد مخصص للاختبار."
    assert out["sources"] == [source]
    retrieve.assert_not_called()
    model.assert_not_called()


def test_failed_grounding_never_returns_retrieved_dump(monkeypatch):
    monkeypatch.setattr(curated, "list_concepts", lambda: [])
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda _: [{"text": "Unrelated fixture text. " * 100, "source": {"chunk_id": "fixture", "source_name": "Fixture", "source_url": "https://example.invalid"}}])
    monkeypatch.setattr(learn.provider, "explain", lambda *args: {"answer": "Unsupported fixture [E99]."})
    out = learn.run_learn("ما معنى أصحاب الفروض؟")
    assert out["decision_state"] == "specialist_referral"
    assert out["source_excerpts"] == []
    assert out["sources"] == []


def test_two_exact_relevant_paragraphs_only():
    paragraphs = ["العصبة: فقرة محايدة للاختبار الأول.", "العصبة: فقرة محايدة للاختبار الثاني.", "العصبة: فقرة محايدة للاختبار الثالث."]
    records = [{"text": "Unrelated neutral preface.\n\n" + p + "\n\nUnrelated neutral ending.", "provenance": {"char_start": 0}} for p in paragraphs]
    output = relevant_public_excerpts("ما معنى العصبة؟", records)
    assert [r["text"] for r in output] == paragraphs[:2]
    assert all("Unrelated" not in r["text"] for r in output)


def test_unverified_catalogue_and_unsupported_concept_abstain(monkeypatch):
    monkeypatch.setattr(curated, "list_concepts", lambda: [{"title_ar": "الحجب", "title_en": "Blocking", "availability": "limited", "short_definition": None, "sources": []}])
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda _: [])
    model = Mock()
    monkeypatch.setattr(learn.provider, "explain", model)
    assert learn.run_learn("ما معنى الحجب؟")["decision_state"] == "specialist_referral"
    model.assert_not_called()
