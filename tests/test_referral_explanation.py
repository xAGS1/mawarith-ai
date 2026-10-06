from copy import deepcopy
import pytest
from backend.pipeline import educational_pipeline as response_pipeline
from backend.pipeline import qwen_pipeline as solver_pipeline


@pytest.fixture
def wife_case(monkeypatch):
    monkeypatch.setattr(solver_pipeline, "retrieve_fiqh", lambda _: [])
    monkeypatch.setattr(solver_pipeline, "enrich_sources", lambda rules: rules)
    return solver_pipeline.run_pipeline("مات وترك زوجة", parsed_relations={
        "mentioned_relatives": [{"relation": "زوجة", "count": 1}]})


@pytest.mark.parametrize("question,language", [("مات وترك زوجة", "ar"), ("A man died leaving a wife", "en")])
def test_wife_only_explains_supported_fixed_share_and_unsupported_remainder(wife_case, question, language):
    before = deepcopy(wife_case)
    response = response_pipeline._run_request(question, "case", case_result=wife_case)
    assert response["decision_state"] == "specialist_referral"
    assert response["language"] == language
    assert response["case_details"]["result"] is None
    assert wife_case["sources"][0]["result"]["fraction"] == "1/4"
    assert wife_case == before
    if language == "ar":
        assert "تم تحديد فرض الزوجة" in response["answer"]
        assert "معالجة الباقي غير مدعومة" in response["answer"]
        assert "لم يُعرض توزيع نهائي" in response["answer"]
    else:
        assert "fixed shares were identified" in response["answer"]
        assert "allocate that remainder is not supported" in response["answer"]


@pytest.mark.parametrize("question,expected", [
    ("مسألة ميراث", "لا تدعم القواعد المتاحة حل هذه المسألة كاملة. يرجى مراجعة مختص بالمواريث."),
    ("Inheritance case", "The available rules do not support a complete solution. Consult an inheritance specialist."),
])
def test_unknown_reason_keeps_generic_fallback(wife_case, question, expected):
    wife_case["case_readiness"]["reason"] = "unknown_future_reason"
    assert response_pipeline._run_request(question, "case", case_result=wife_case)["answer"] == expected


def test_excess_fixed_shares_are_not_described_as_a_remainder(wife_case):
    wife_case["sources"][0]["result"]["fraction"] = "3/2"
    answer = response_pipeline._run_request("مسألة ميراث", "case", case_result=wife_case)["answer"]
    assert answer.startswith("لا تدعم القواعد المتاحة")
