from unittest.mock import patch

import pytest

from backend.app import CaseRequest, analyze_case_endpoint
from backend.pipeline.qwen_pipeline import run_pipeline
from backend.rag.coverage import check_source_coverage


@pytest.mark.parametrize("through_api", [False, True])
def test_unsupported_brother_blocks_reasoner_and_verifier(through_api):
    question = "مات وترك زوجة وأخا شقيقا."
    parsed = {"mentioned_relatives": [
        {"relation": "زوجة", "count": 1},
        {"relation": "أخ شقيق", "count": 1},
    ]}
    with (
        patch("backend.pipeline.qwen_pipeline.parse_relations", return_value=parsed),
        patch("backend.pipeline.qwen_pipeline.analyze_case") as reasoner,
        patch("backend.pipeline.qwen_pipeline.verify_and_normalize") as verifier,
    ):
        if through_api:
            output = analyze_case_endpoint(CaseRequest(question=question)).model_dump()
        else:
            output = run_pipeline(question)

    reasoner.assert_not_called()
    verifier.assert_not_called()
    assert output["question"] == question
    assert output["parsed_relations"] == parsed
    assert output["case_features"]["has_descendant"] is False
    assert [rule["rule_id"] for rule in output["sources"]] == ["wife_without_descendant"]
    assert output["source_coverage"] == {
        "is_sufficient": False,
        "covered_relations": ["زوجة"],
        "unsupported_relations": ["أخ شقيق"],
        "coverage_ratio": 0.5,
    }
    assert output["decision_state"] == "insufficient_sources"
    assert output["result"] is None


@pytest.mark.parametrize("relations,rules,expected", [
    (["زوجة", "ابن", "ابن", "بنت"], [{"conditions": {}, "applies_to": ["زوجة", "ابن", "بنت"]}],
     {"is_sufficient": True, "covered_relations": ["زوجة", "ابن", "بنت"], "unsupported_relations": [], "coverage_ratio": 1.0}),
    (["بنت ابن"], [{"conditions": {}, "applies_to": ["بنت"]}],
     {"is_sufficient": False, "covered_relations": [], "unsupported_relations": ["بنت ابن"], "coverage_ratio": 0.0}),
    (["أم"], [],
     {"is_sufficient": False, "covered_relations": [], "unsupported_relations": ["أم"], "coverage_ratio": 0.0}),
    ([], [{"conditions": {}, "applies_to": ["زوجة"]}],
     {"is_sufficient": False, "covered_relations": [], "unsupported_relations": [], "coverage_ratio": 0.0}),
    (["زوجة"], [{}],
     {"is_sufficient": False, "covered_relations": [], "unsupported_relations": ["زوجة"], "coverage_ratio": 0.0}),
])
def test_coverage_uses_distinct_exact_relations_and_fails_closed(relations, rules, expected):
    parsed = {"mentioned_relatives": [{"relation": relation, "count": 2} for relation in relations]}
    assert check_source_coverage(parsed, rules) == expected


def test_empty_case_never_calls_reasoner():
    with (
        patch("backend.pipeline.qwen_pipeline.parse_relations", return_value={"mentioned_relatives": []}),
        patch("backend.pipeline.qwen_pipeline.analyze_case") as reasoner,
    ):
        output = run_pipeline("")
    reasoner.assert_not_called()
    assert output["decision_state"] == "insufficient_sources"
    assert output["result"] is None
