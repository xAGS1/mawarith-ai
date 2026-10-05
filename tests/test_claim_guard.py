import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.pipeline.claim_guard import guard_claims, GENERAL_AR, HEIR_AR
from backend.pipeline import learn_pipeline as learn


def rules(*ids):
    records = json.loads((Path(__file__).resolve().parents[1] / "data/sources/inheritance_rules.json").read_text(encoding="utf-8"))
    return [r for r in records if r["rule_id"] in ids]


def test_daughter_supported_brother_abstains():
    confirmed = rules("one_daughter_without_son")
    answer = "الحالة تتضمن بنتًا وأخًا. البنت تأخذ النصف. الأخ يحصل على السدس."
    result = guard_claims(answer, confirmed_rules=confirmed)
    assert "الحالة تتضمن بنتًا وأخًا." in result["answer"]
    assert "البنت تأخذ النصف." in result["answer"]
    assert HEIR_AR in result["answer"]
    assert "السدس" not in result["answer"]
    assert len(result["blocked_claims"]) == 1


@pytest.mark.parametrize("claim", [
    "الأخ يأخذ الباقي.", "الأخ يحصل على السدس.", "الأخ لا يرث.",
    "الأخ الشقيق يرث الباقي.", "الأخت لأب تأخذ النصف.",
    "هذه المسألة فيها عول.", "هذه المسألة فيها الرد.",
    "التوزيع النهائي هو 1/2 للأخ.", "الأخ يرث إذا وجدت البنت.",
    "The brother receives the remainder.", "The brother gets 1/6.",
])
def test_sensitive_claim_categories_require_support(claim):
    result = guard_claims(claim, confirmed_rules=rules("one_daughter_without_son"))
    assert result["blocked_claims"] == [claim]
    assert claim not in result["answer"]


def test_fraction_or_heir_mention_in_evidence_does_not_grant_entitlement():
    evidence = [{"evidence_id": "E1", "text": "Neutral fixture: brother, daughter, 1/6."}]
    result = guard_claims("The brother receives 1/6 [E1].", evidence, language="en")
    assert result["blocked_claims"]
    assert "1/6" not in result["answer"]


def test_supported_simple_case_statements_unchanged():
    confirmed = rules("wife_with_descendant", "mother_with_child", "sons_and_daughters")
    answer = "الزوجة تأخذ الثمن من الميراث. الأم تأخذ السدس من الميراث.\n" + next(r["rule"] for r in confirmed if r["rule_id"] == "sons_and_daughters")
    assert guard_claims(answer, confirmed_rules=confirmed)["answer"] == answer


def test_wrong_fraction_and_added_condition_are_blocked():
    confirmed = rules("wife_with_descendant")
    for claim in ("الزوجة تأخذ الربع.", "الزوجة تأخذ الثمن إذا لم يوجد ولد."):
        assert guard_claims(claim, confirmed_rules=confirmed)["blocked_claims"] == [claim]


def test_source_sentence_cannot_borrow_another_citation():
    claim = rules("one_daughter_without_son")[0]["rule"]
    evidence = [{"evidence_id": "E1", "text": "Neutral fixture."}, {"evidence_id": "E2", "text": claim}]
    assert guard_claims(claim + " [E2]", evidence)["blocked_claims"] == []
    assert guard_claims(claim + " [E1]", evidence)["blocked_claims"]


def test_no_evidence_abstains_but_presentation_text_is_harmless():
    assert guard_claims("الأخ يأخذ الباقي.")["answer"] == HEIR_AR
    assert guard_claims("")["answer"] == GENERAL_AR
    text = "الحالة تتضمن بنتًا وأخًا. بحسب الأدلة المرفقة..."
    assert guard_claims(text)["answer"] == text


def test_partial_learn_answer_preserves_supported_statement_only(monkeypatch):
    rule = rules("one_daughter_without_son")[0]
    hit = {"text": rule["rule"], "source": {"chunk_id": "fixture", "source_name": "Fixture",
           "source_url": "https://example.invalid", "section": "Fixture"}}
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda q: [hit])
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    monkeypatch.setattr(learn.provider, "explain", Mock(return_value={
        "answer": rule["rule"] + " [E1]\nالأخ يأخذ الباقي [E1].",
        "key_concepts": [{"term": "الأخ", "explanation": "الأخ يأخذ الباقي [E1]."}]}))
    result = learn.run_learn("اشرح حالة بنت وأخ")
    assert result["decision_state"] == "ready"
    assert rule["rule"] in result["answer"]
    assert "الأخ يأخذ الباقي" not in result["answer"]
    assert HEIR_AR in result["answer"]
    assert result["key_concepts"] == []


def test_entirely_unsupported_learn_answer_abstains(monkeypatch):
    hit = {"text": "Neutral fixture.", "source": {"chunk_id": "fixture", "source_name": "Fixture",
           "source_url": "https://example.invalid", "section": "Fixture"}}
    monkeypatch.setattr(learn, "retrieve_educational_evidence", lambda q: [hit])
    monkeypatch.setattr(learn.provider, "explain", Mock(return_value={"answer": "الأخ يأخذ الباقي [E1]."}))
    result = learn.run_learn("اشرح حالة بنت وأخ")
    assert result["evidence_status"] == "insufficient"
    assert result["source_excerpts"] == []
    assert "الأخ يأخذ الباقي" not in result["answer"]
