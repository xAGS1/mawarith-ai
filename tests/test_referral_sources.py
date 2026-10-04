"""Referral source display uses neutral synthetic evidence only."""
import json
from copy import deepcopy

import pytest

from backend.pipeline import educational_pipeline as pipeline


def noisy_hit():
    source = {"chunk_id": "unrelated", "source_name": "Synthetic fixture",
              "section": "Unrelated", "source_url": "https://example.invalid"}
    return {"score": 0.99, "text": "UNRELATED MAIN FIXTURE", "source": source,
            "previous_chunk": {"text": "UNRELATED PREVIOUS FIXTURE", "source": {**source, "chunk_id": "previous"}},
            "next_chunk": {"text": "UNRELATED NEXT FIXTURE", "source": {**source, "chunk_id": "next"}}}


def internal_case(state="specialist_referral", sources=None):
    return {"decision_state": state, "result": None, "sources": sources or [],
            "fiqh_evidence": [noisy_hit()], "fiqh_retrieval": {"status": "available"}}


def test_referral_omits_unverified_hits_and_neighbors_everywhere_public(monkeypatch):
    case = internal_case()
    case["fiqh_retrieval"]["error"] = "UNRELATED RAW PAYLOAD FIXTURE"
    original = deepcopy(case)
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: case)
    out = pipeline.run_request("Unsupported case", "case")
    assert out["decision_state"] == "specialist_referral"
    assert out["source_excerpts"] == []
    assert out["case_details"]["fiqh_evidence"] == []
    assert out["case_details"]["fiqh_retrieval"] == {"status": "available"}
    assert "UNRELATED" not in json.dumps(out)
    assert case == original  # Internal retrieval remains available for debugging.


def test_referral_retains_only_confirmed_rule_source_text(monkeypatch):
    rule = {"rule_id": "confirmed_fixture_rule", "topic": "Neutral fixture topic",
            "rule": "Neutral structured fixture description", "source": {
                "source_type": "quran", "source_name": "Synthetic adapter fixture",
                "reference": "4:12", "arabic_text": "EXACT ADAPTER FIXTURE",
                "immutable_text": True}}
    case = internal_case(sources=[rule])
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: case)
    out = pipeline.run_request("Unsupported case", "case")
    assert out["sources"] == [rule]
    assert [e["text"] for e in out["source_excerpts"]] == ["EXACT ADAPTER FIXTURE"]
    assert out["key_concepts"][0]["explanation"] == rule["rule"]
    assert "UNRELATED" not in json.dumps(out)


def test_unavailable_rule_source_does_not_create_an_excerpt(monkeypatch):
    rule = {"rule_id": "fixture", "topic": "Neutral", "rule": "Neutral description",
            "source": {"source_type": "quran", "reference": "4:12", "retrieval_status": "unavailable"}}
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: internal_case(sources=[rule]))
    out = pipeline.run_request("Unsupported case", "case")
    assert out["sources"] == [rule]
    assert out["source_excerpts"] == []


@pytest.mark.parametrize("state", ["ready", "needs_clarification", "out_of_scope"])
def test_other_case_states_keep_existing_source_display(state, monkeypatch):
    case = internal_case(state)
    if state == "ready":
        case["result"] = {"verification": {"is_consistent": True}}
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: case)
    out = pipeline.run_request("Test case", "case")
    assert out["decision_state"] == state
    assert len(out["source_excerpts"]) == 3
    assert out["case_details"]["fiqh_evidence"] == case["fiqh_evidence"]


def test_inconsistent_result_mapped_to_referral_also_filters(monkeypatch):
    case = internal_case("ready")
    case["result"] = {"verification": {"is_consistent": False}}
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: case)
    out = pipeline.run_request("Test case", "case")
    assert out["decision_state"] == "specialist_referral"
    assert out["source_excerpts"] == []
    assert out["case_details"]["result"] is None
    assert "UNRELATED" not in json.dumps(out)


def test_learn_response_is_unchanged(monkeypatch):
    expected = {"mode": "learn", "source_excerpts": [{"text": "Neutral learn fixture"}]}
    monkeypatch.setattr(pipeline, "run_learn", lambda q: expected)
    assert pipeline.run_request("Test", "learn") == expected


@pytest.mark.parametrize("state", ["ready", "specialist_referral"])
def test_shared_source_reference_displayed_once_rules_preserved(state, monkeypatch):
    source = {"source_type": "quran", "source_name": "Synthetic adapter fixture",
              "reference": "4:11", "arabic_text": "EXACT NEUTRAL FIXTURE",
              "immutable_text": True}
    rules = [{"rule_id": "first", "topic": "Neutral", "rule": "First fixture rule", "source": deepcopy(source)},
             {"rule_id": "second", "topic": "Neutral", "rule": "Second fixture rule", "source": deepcopy(source)},
             {"rule_id": "different_reference", "topic": "Neutral", "rule": "Third fixture rule",
              "source": {**source, "reference": "4:12", "arabic_text": "OTHER NEUTRAL FIXTURE"}},
             {"rule_id": "different_source", "topic": "Neutral", "rule": "Fourth fixture rule",
              "source": {**source, "source_name": "Another source"}}]
    case = internal_case(state, rules)
    case["fiqh_evidence"] = []
    if state == "ready":
        case["result"] = {"verification": {"is_consistent": True}}
    original = deepcopy(case)
    monkeypatch.setattr(pipeline, "run_pipeline", lambda q: case)
    out = pipeline.run_request("Test case", "case")
    assert out["decision_state"] == state
    assert out["sources"] == rules
    assert len(out["source_excerpts"]) == 3
    assert [e["reference"] for e in out["source_excerpts"]] == ["4:11", "4:12", "4:11"]
    assert out["source_excerpts"][0]["text"] == source["arabic_text"]
    assert case == original
