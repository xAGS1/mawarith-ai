"""Replay the observed model failure through production learning code."""
from pathlib import Path
from unittest.mock import Mock
import pytest
from backend.learning import definition_retrieval as router
from backend.pipeline import learn_pipeline as learn


def test_local_uqu_definition_survives_unsupported_model_addition(monkeypatch):
    raw = Path(__file__).resolve().parents[1] / "data/fiqh/uqu_mawarith_1/raw"
    if not (raw / "mawarith_course-uqu.pdf").exists():
        pytest.skip("Approved local UQU PDF is not redistributed")
    monkeypatch.setattr(router, "UQU_DIR", raw)
    monkeypatch.setattr(learn, "retrieve_educational_evidence", Mock(side_effect=AssertionError("Unexpected fallback")))
    # Actual recorded production Qwen output, not approved religious content.
    generated = "العصبة تعني الإرث بغير تقدير، أي أن الورثة يحصلون على ما تبقى من الميراث بعد توزيع الفروض."
    model = Mock(return_value={"status": "ready", "answer": generated,
        "key_concepts": [{"term": "العصبة", "explanation": generated + " [E1]"}]})
    monkeypatch.setattr(learn.provider, "explain", model)
    guard = Mock(wraps=learn.guard_claims)
    monkeypatch.setattr(learn, "guard_claims", guard)
    result = learn.run_learn("ما معنى العصبة؟")
    assert result["evidence_status"] == "supported"
    assert result["answer"] == "اصطلاحا: الإرث بغير تقدير."
    assert result["source_excerpts"][0]["text"] == "اصطلاحا: الإرث بغير تقدير.  "
    assert result["sources"][0]["source_id"] == "uqu_mawarith_1"
    assert result["sources"][0]["page"] == 13
    assert result["key_concepts"] == []
    assert "الفروض" not in result["answer"]
    assert guard.call_count >= 2
    assert learn.guard_claims(generated, result["source_excerpts"])["blocked_claims"]


def test_behavior_only_evidence_still_abstains(monkeypatch):
    monkeypatch.setattr(router, "uqu_candidates", lambda _: [])
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda _: [{
        "text": "العصبة هو يأخذ الباقي.", "source": {"verified_source": True}}])
    model = Mock()
    monkeypatch.setattr(learn.provider, "explain", model)
    assert learn.run_learn("ما معنى العصبة؟")["evidence_status"] == "insufficient"
    model.assert_not_called()
