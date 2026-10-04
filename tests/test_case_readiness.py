from unittest.mock import Mock

import pytest

from backend.pipeline import educational_pipeline as shared
from backend.pipeline import qwen_pipeline as pipeline
from backend.rules.case_readiness import assess_case
from tests.test_qwen_pipeline import PARSED, QUESTION, model_result


@pytest.fixture
def isolated_case(monkeypatch):
    monkeypatch.setattr(pipeline, "enrich_sources", lambda rules: rules)
    monkeypatch.setattr(pipeline, "retrieve_fiqh", lambda q: [])
    reasoner = Mock(return_value=model_result())
    monkeypatch.setattr(pipeline, "analyze_case", reasoner)
    verifier = Mock(wraps=pipeline.verify_and_normalize)
    monkeypatch.setattr(pipeline, "verify_and_normalize", verifier)
    return reasoner, verifier


def parsed(*relations):
    return {"mentioned_relatives": [{"relation": r, "count": n} for r, n in relations]}


@pytest.mark.parametrize("question", ["ترك بنتًا وأخًا", "A person died leaving a daughter and a brother."])
def test_ambiguous_brother_never_calls_reasoner(question, isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: parsed(("بنت", 1), ("أخ", 1)))
    output = shared.run_request(question, "case")
    assert output["decision_state"] == "needs_clarification"
    assert output["clarification_question"]
    assert output["case_details"]["result"] is None
    assert output["sources"]  # The supported daughter rule is retained.
    assert output["key_concepts"]
    for mock in isolated_case:
        mock.assert_not_called()


def test_raw_ambiguity_cannot_be_hidden_by_parser_guess(isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: parsed(("بنت", 1), ("أخ شقيق", 1)))
    out = shared.run_request("ترك بنتًا وأخًا", "case")
    assert out["decision_state"] == "needs_clarification"
    isolated_case[0].assert_not_called()


@pytest.mark.parametrize("question", ["مات وترك زوجة وأبناء، وعدد الأبناء غير معروف.",
    "A man died leaving a wife and sons; the number of sons is unknown.",
    "مات وترك زوجة وأطفالا.", QUESTION + " وهناك ورثة آخرون غير مذكورين."])
def test_missing_impactful_information(question, isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: PARSED)
    out = shared.run_request(question, "case")
    assert out["decision_state"] == "needs_clarification"
    assert out["clarification_question"]
    isolated_case[0].assert_not_called()


def test_advanced_case_refers_before_reasoning(isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: PARSED)
    out = shared.run_request(QUESTION + " والزوجة حامل.", "case")
    assert out["decision_state"] == "specialist_referral"
    assert out["clarification_question"] is None
    assert out["case_details"]["result"] is None
    assert out["sources"] and out["answer"]
    isolated_case[0].assert_not_called()


@pytest.mark.parametrize("relatives", [
    (("أب", 1), ("بنت", 1)),
    (("زوج", 1), ("أم", 1), ("بنت", 2)),
    (("زوجة", 1),),
    (("عمة", 1),),
])
def test_uncovered_complete_case_never_forces_calculation(relatives, isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: parsed(*relatives))
    out = shared.run_request("مسألة ميراث", "case")
    assert out["decision_state"] == "specialist_referral"
    assert out["case_details"]["result"] is None
    isolated_case[0].assert_not_called()


def test_supported_case_still_runs_solver_and_verifier(isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: PARSED)
    out = shared.run_request(QUESTION, "case")
    assert out["decision_state"] == "ready"
    assert out["clarification_question"] is None
    assert out["case_details"]["result"]["verification"]["is_consistent"] is True
    for mock in isolated_case:
        mock.assert_called_once()


def test_unknown_requested_share_is_not_missing_family_information():
    out = assess_case(QUESTION + " لا أعرف نصيب الابن.", PARSED, [])
    assert out["decision_state"] == "ready"


def test_out_of_scope_and_empty_case(isolated_case, monkeypatch):
    monkeypatch.setattr(pipeline, "parse_relations", lambda q: parsed())
    assert shared.run_request("What is the weather?", "case")["decision_state"] == "out_of_scope"
    empty = shared.run_request("", "case")
    assert empty["decision_state"] == "needs_clarification"
    assert empty["clarification_question"]
    isolated_case[0].assert_not_called()


def test_learn_dispatch_is_unchanged(monkeypatch):
    result = {"mode": "learn", "answer": "Unchanged explanation"}
    learn = Mock(return_value=result)
    case = Mock()
    monkeypatch.setattr(shared, "run_learn", learn)
    monkeypatch.setattr(shared, "run_pipeline", case)
    assert shared.run_request("What is a fixed share?", "learn") == result
    learn.assert_called_once()
    case.assert_not_called()
