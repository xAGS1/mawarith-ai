from copy import deepcopy
from unittest.mock import Mock

import pytest
import requests

from backend.llm import qwen_understanding
from backend.llm.qwen_understanding import understand_input as classify_transport, select_claims as selection_transport
from backend.pipeline import educational_pipeline as shared
from backend.pipeline import understanding as understanding_layer
from backend.pipeline import qwen_pipeline as cases
from backend.pipeline.case_explanation import explain_case_question
from backend.pipeline.evidence_plan import build_evidence_plan
from tests.test_qwen_pipeline import PARSED, model_result


@pytest.mark.parametrize("question,intent", [
    ("ما معنى العصبة؟", "learn_concept"),
    ("ما الفرق بين الفرض والتعصيب؟", "compare_concepts"),
    ("توفي رجل وترك زوجة وأم وابنين وبنت", "inheritance_case"),
    ("توفي رجل وترك زوجة وأم وابنين وبنت، لماذا يختلف نصيب الابن عن البنت؟", "mixed_case_and_question"),
    ("What is the difference between fixed shares and residuary inheritance?", "compare_concepts"),
    ("What is the weather?", "out_of_scope"),
])
def test_intents_ai_and_deterministic_fallback(monkeypatch, question, intent):
    result, origin = understanding_layer.understand(question)
    assert result.intent == intent
    assert origin == "deterministic_fallback"
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=result.model_dump()))
    ai, origin = understanding_layer.understand(question)
    assert ai.intent == intent
    assert origin == "ai"


@pytest.mark.parametrize("invalid", [
    {"intent": "invented"}, {"intent": "learn_concept", "language": "ar", "shares": "1/2"},
    {"intent": "learn_concept", "language": "ar", "educational_question": "invented question"},
])
def test_invalid_ai_output_falls_back(monkeypatch, invalid):
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=invalid))
    result, origin = understanding_layer.understand("ما معنى العصبة؟")
    assert origin == "deterministic_fallback"
    assert result.intent == "learn_concept"


def test_explicit_case_facts_and_language_cannot_be_overridden(monkeypatch):
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value={
        "intent": "out_of_scope", "language": "en", "deceased_gender": "female"}))
    result, _ = understanding_layer.understand("توفي رجل وترك زوجة وأم وابنين وبنت")
    assert result.intent == "inheritance_case"
    assert result.language == "ar"
    assert result.deceased_gender == "male"


def test_depth_and_question_kind():
    result = understanding_layer.fallback_understanding("Explain in detail how residuary inheritance works")
    assert result.depth == "detailed"
    assert result.question_kind == "how"


def test_ai_ambiguity_is_advisory_and_readiness_confirms(monkeypatch):
    question = "ترك بنتًا وأخًا"
    advisory = understanding_layer.fallback_understanding(question).model_dump()
    advisory["ambiguity_candidates"] = ["sibling_type", "unconfirmed_count"]
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=advisory))
    monkeypatch.setattr(cases, "parse_relations", lambda q: {"mentioned_relatives": [
        {"relation": "بنت", "count": 1}, {"relation": "أخ", "count": 1}]})
    monkeypatch.setattr(cases, "enrich_sources", lambda rules: rules)
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda q: [])
    reasoner = Mock(side_effect=AssertionError("Must not calculate ambiguous case"))
    monkeypatch.setattr(cases, "analyze_case", reasoner)
    trace = {}
    result = shared.run_request(question, "case", debug_trace=trace)
    assert result["decision_state"] == "needs_clarification"
    assert result["case_details"]["result"] is None
    assert trace["readiness_confirmation"]["reason"] == "ambiguous_sibling"
    assert trace["ambiguity_candidates"] == advisory["ambiguity_candidates"]
    reasoner.assert_not_called()
    assert "debug_trace" not in result


def test_mixed_case_keeps_solver_output_and_answers_why(monkeypatch):
    question = "توفي رجل وترك زوجة وأم وابنين وبنت، لماذا يختلف نصيب الابن عن البنت؟"
    monkeypatch.setattr(cases, "parse_relations", lambda q: deepcopy(PARSED))
    monkeypatch.setattr(cases, "enrich_sources", lambda rules: rules)
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda q: [])
    reasoner = Mock(return_value=model_result())
    monkeypatch.setattr(cases, "analyze_case", reasoner)
    select = Mock(return_value={"claim_ids": ["C3"]})
    # Use IDs from the actual matched rule plan rather than assume its ordering.
    select.side_effect = lambda q, lang, depth, claims: {"claim_ids": [claims[0]["claim_id"]]}
    monkeypatch.setattr(qwen_understanding, "select_claims", select)
    baseline = cases.run_pipeline(question)
    trace = {}
    response = shared.run_request(question, "case", debug_trace=trace)
    assert response["decision_state"] == "ready"
    assert response["case_details"]["result"] == baseline["result"]
    assert response["case_details"]["result"]["verification"]["is_consistent"]
    expected = next(r["rule"] for r in baseline["sources"] if r["rule_id"] == "sons_and_daughters")
    assert expected in response["answer"]
    assert trace["detected_intent"] == "mixed_case_and_question"
    assert trace["parsed_entities"] == PARSED
    assert trace["explanation_claims"][0]["concept_or_rule_id"] == "sons_and_daughters"
    assert trace["selected_source_ids"]
    select.assert_called_once()
    assert "ambiguity_candidates" not in response
    assert "explanation_claims" not in response


def test_unsupported_claim_ids_cannot_invent_rulings(monkeypatch):
    plan = [{"claim_id": "C1", "concept_or_rule_id": "neutral", "source_id": "fixture:1",
             "statement": "Neutral verified fixture statement.", "support": "structured", "applies_to": []}]
    monkeypatch.setattr(qwen_understanding, "select_claims", Mock(return_value={"claim_ids": ["C99"], "answer": "Invented"}))
    understanding = understanding_layer.fallback_understanding("Why this inheritance rule?")
    answer, claims, origin = explain_case_question("Why this rule?", understanding, plan)
    assert "Invented" not in answer
    assert plan[0]["statement"] in answer
    assert origin == "deterministic_fallback"
    assert claims == plan


def test_source_text_and_support_associations_stay_exact():
    text = "Neutral exact fixture.\n  Spacing preserved."
    rule = {"rule_id": "neutral", "rule": "Neutral statement", "source": {
        "source_type": "fixture", "reference": "1", "arabic_text": text, "immutable_text": True}}
    plan = build_evidence_plan([rule], [{"concept_id": "neutral_concept", "evidence_id": "E1", "text": text}])
    assert plan[0]["exact_excerpt"] == text
    assert plan[0]["support"] == "structured"
    assert plan[1]["support"] == "retrieved"
    assert plan[1]["source_id"] == "E1"
    assert plan[1]["concept_or_rule_id"] == "neutral_concept"
    assert plan[1]["statement"] is None


def test_explicit_learn_mode_not_rerouted(monkeypatch):
    response = {"mode": "learn", "answer": "Neutral answer"}
    monkeypatch.setattr(shared, "run_learn", lambda q: response)
    solver = Mock(side_effect=AssertionError("Explicit learn mode must stay learn"))
    monkeypatch.setattr(shared, "run_pipeline", solver)
    assert shared.run_request("توفي رجل وترك بنتا", "learn") == response
    solver.assert_not_called()


def test_ai_ambiguity_cannot_force_referral_on_supported_case(monkeypatch):
    question = "توفي رجل وترك زوجة وأم وابنين وبنت"
    advisory = understanding_layer.fallback_understanding(question).model_dump()
    advisory["ambiguity_candidates"] = ["possible_unknown_count"]
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=advisory))
    monkeypatch.setattr(cases, "parse_relations", lambda q: deepcopy(PARSED))
    monkeypatch.setattr(cases, "enrich_sources", lambda rules: rules)
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda q: [])
    monkeypatch.setattr(cases, "analyze_case", Mock(return_value=model_result()))
    trace = {}
    result = shared.run_request(question, "case", debug_trace=trace)
    assert result["decision_state"] == "ready"
    assert trace["readiness_confirmation"]["decision_state"] == "ready"
    assert trace["ambiguity_candidates"] == advisory["ambiguity_candidates"]


def test_new_qwen_transports_are_bounded_and_do_not_request_rulings(monkeypatch):
    response = Mock()
    response.json.return_value = {"response": '{"intent":"learn_concept","language":"en"}'}
    post = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post)
    schema = understanding_layer.Understanding.model_json_schema()
    assert classify_transport("What is a residuary heir?", schema)["intent"] == "learn_concept"
    payload = post.call_args.kwargs["json"]
    assert payload["format"]["additionalProperties"] is False
    assert payload["think"] is False
    assert payload["options"]["temperature"] == 0
    assert post.call_args.kwargs["timeout"] == (5, 45)
    assert "Do not" in payload["system"]
    response.json.return_value = {"response": '{"claim_ids":["C1"]}'}
    assert selection_transport("Why?", "en", "simple", []) == {"claim_ids": ["C1"]}
    assert post.call_args.kwargs["json"]["format"]["additionalProperties"] is False


def test_request_context_is_reset_after_failure(monkeypatch):
    monkeypatch.setattr(shared, "run_learn", Mock(side_effect=ValueError("Fixture failure")))
    with pytest.raises(ValueError, match="Fixture failure"):
        shared.run_request("What is a fixed share?", debug_trace={})
    assert understanding_layer.CURRENT_UNDERSTANDING.get() is None
    assert understanding_layer.CURRENT_TRACE.get() is None
