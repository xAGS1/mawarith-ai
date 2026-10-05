from unittest.mock import Mock
import pytest
from backend.pipeline.request_classifier import classify_request
from backend.pipeline.understanding import Understanding
from backend.pipeline import educational_pipeline as shared


@pytest.mark.parametrize("question, expected", [
    ("ما معنى العصبة؟", "educational"),
    ("ما الفرق بين الفرض والتعصيب؟", "educational"),
    ("عرّف الحجب", "educational"),
    ("من هم أصحاب الفروض؟", "educational"),
    ("لماذا توجد أنصبة محددة؟", "educational"),
    ("مات وترك ابنان فقط", "calculation"),
    ("توفي رجل وترك زوجة وأم وابنين وبنت", "calculation"),
    ("احسب نصيب كل وارث", "calculation"),
    ("قسم التركة", "calculation"),
    ("كم نصيب الأم؟", "calculation"),
    ("وزّع التركة", "calculation"),
    ("لو فيه بنت وأخ وش يصير؟", "calculation"),
    ("What is a residuary heir?", "educational"),
    ("A man died leaving a wife and two sons", "calculation"),
    ("Calculate the inheritance shares", "calculation"),
])
def test_explicit_indicators_override_advice(question, expected):
    contrary = Understanding(intent="inheritance_case" if expected == "educational" else "learn_concept", language="ar")
    assert classify_request(question, contrary)[0] == expected


def test_ambiguous_case_advice_is_bounded():
    advice = Understanding(intent="inheritance_case", language="ar")
    assert classify_request("لو فيه بنت وأخ", advice) == ("calculation", "advisory_case")
    assert classify_request("لو فيه بنت وأخ")[0] == "educational"
    assert classify_request("ما معنى العصبة؟", advice)[0] == "educational"
    assert classify_request("سؤال غير محدد", advice)[0] == "educational"


@pytest.mark.parametrize("question, mode, expected", [
    ("ما معنى العصبة؟", None, "learn"),
    ("ما الفرق بين الفرض والتعصيب؟", None, "learn"),
    ("مات وترك ابنان فقط", None, "case"),
    ("لو فيه بنت وأخ وش يصير؟", None, "case"),
    ("توفي رجل وترك زوجة وأم وابنين وبنت", "learn", "learn"),
    ("ما معنى العصبة؟", "case", "case"),
])
def test_production_entry_dispatch_and_schema_unchanged(question, mode, expected, monkeypatch):
    result = {"mode": expected, "decision_state": "needs_clarification", "answer": "Synthetic response", "case_details": None}
    dispatch = Mock(return_value=result)
    monkeypatch.setattr(shared, "_run_request", dispatch)
    trace = {}
    output = shared.run_request(question, mode, debug_trace=trace)
    dispatch.assert_called_once_with(question, expected)
    assert output == result
    assert "request_type" not in output and "response_type" not in output
    assert trace["request_type"] == ("calculation" if expected == "case" else "educational")
    assert trace["response_type"] == ("calculation_result" if expected == "case" else "educational_explanation")
    if mode:
        assert trace["routing_origin"] == "explicit_api_mode"


def test_empty_inferred_request_uses_existing_clarification():
    result = shared.run_request("")
    assert result["mode"] == "learn"
    assert result["decision_state"] == "needs_clarification"
    assert result["case_details"] is None


def test_invalid_mode_rejected():
    with pytest.raises(ValueError):
        shared.run_request("question", "invalid")
