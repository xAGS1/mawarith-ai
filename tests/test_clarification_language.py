"""Clarification-only language guarantees at the production response boundary."""
from unittest.mock import Mock
import pytest
from backend.pipeline import educational_pipeline as pipeline
from backend.llm import qwen_understanding

UNDERSTAND_TRANSPORT = qwen_understanding.understand_input


@pytest.mark.parametrize("question,language", [("لفظ غامض", "Arabic"), ("unclear", "English")])
def test_clarification_prompt_requests_query_language(question, language, monkeypatch):
    captured = {}
    response = Mock()
    response.json.return_value = {"response": "{}"}
    def post(*args, **kwargs):
        captured.update(kwargs["json"])
        return response
    monkeypatch.setattr(qwen_understanding, "generation_post", post)
    UNDERSTAND_TRANSPORT(question, {"properties": {"retrieval_query": {}}})
    assert f"write clarification_question in {language}" in captured["system"]
    assert "Do not switch to another language" in captured["system"]


@pytest.mark.parametrize("question,language,clarification,expected", [
    ("خلا", "en", "Could you clarify your question?", "لم أفهم المقصود من سؤالك. هل يمكنك توضيحه أكثر؟"),
    ("لفظ غامض", "ar", "Could you clarify what غامض means?", "لم أفهم المقصود من سؤالك. هل يمكنك توضيحه أكثر؟"),
    ("كلمة غير واضحة", "ar", "هل يمكنك توضيح المقصود؟", "هل يمكنك توضيح المقصود؟"),
    ("unclear", "ar", "هل يمكنك التوضيح؟", "I couldn't determine the intended meaning. Could you clarify your question?"),
    ("unclear", "en", "Could you clarify your question?", "Could you clarify your question?"),
    ("غامض", "ar", None, "لم أفهم المقصود من سؤالك. هل يمكنك توضيحه أكثر؟"),
])
def test_production_clarification_language(question, language, clarification, expected, monkeypatch):
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value={
        "intent": "clarification_needed", "language": language, "topic": "",
        "retrieval_query": "", "concepts": [], "case": None,
        "clarification_question": clarification,
    }))
    response = pipeline.run_request(question, "learn")
    assert response["decision_state"] == "needs_clarification"
    assert response["language"] == ("ar" if any("\u0600" <= c <= "\u06ff" for c in question) else "en")
    assert response["clarification_question"] == expected
    assert response["answer"] == expected


@pytest.mark.parametrize("state", ["ready", "specialist_referral", "out_of_scope"])
def test_other_states_are_unchanged(state, monkeypatch):
    response = {"decision_state": state, "language": "en", "answer": "Existing answer", "clarification_question": None}
    monkeypatch.setattr(pipeline, "_answer_request", lambda *args, **kwargs: dict(response))
    assert pipeline.run_request("سؤال عربي") == response
