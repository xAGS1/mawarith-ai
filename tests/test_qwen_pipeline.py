import json
from fractions import Fraction
from unittest.mock import Mock, patch

import pytest

from backend.app import CaseRequest, analyze_case_endpoint
from backend.llm.qwen_reasoner import analyze_case
from backend.pipeline.qwen_pipeline import run_pipeline
from backend.rag.retriever import RULES_PATH, retrieve_rules


QUESTION = "مات وترك زوجة وأما وابنين وبنت. ما هو نصيب كل وريث؟"
PARSED = {
    "mentioned_relatives": [
        {"relation": "زوجة", "count": 1},
        {"relation": "أم", "count": 1},
        {"relation": "ابن", "count": 2},
        {"relation": "بنت", "count": 1},
    ]
}


def model_result():
    return {
        "heirs": [
            {"heir": item["relation"], "count": item["count"]}
            for item in PARSED["mentioned_relatives"]
        ],
        "blocked": [],
        "shares": [
            {"heir": "زوجة", "count": 1, "fraction": "1/8"},
            {"heir": "أم", "count": 1, "fraction": "1/6"},
            {"heir": "ابن", "count": 2, "fraction": "17/30"},
            {"heir": "بنت", "count": 1, "fraction": "17/120"},
        ],
        "awl_or_radd": "لا",
        "post_tasil": {
            "distribution": [
                {"heir": "زوجة", "count": 1, "per_head_shares": "1/8"},
                {"heir": "أم", "count": 1, "per_head_shares": "1/6"},
                {"heir": "ابن", "count": 2, "per_head_shares": "17/60"},
                {"heir": "بنت", "count": 1, "per_head_shares": "17/120"},
            ]
        },
    }


def response_for(result):
    response = Mock()
    response.json.return_value = {"response": json.dumps(result, ensure_ascii=False)}
    return response


@pytest.mark.parametrize("through_api", [False, True])
def test_full_pipeline_and_api_preserve_sources_and_verification(through_api):
    # Mock only model transport: the real parser, retriever, reasoner and verifier run.
    with patch("requests.post", side_effect=[response_for(PARSED), response_for(model_result())]) as post:
        if through_api:
            output = analyze_case_endpoint(CaseRequest(question=QUESTION)).model_dump()
        else:
            output = run_pipeline(QUESTION)

    assert output["question"] == QUESTION
    assert output["parsed_relations"] == PARSED
    assert output["sources"] == json.loads(RULES_PATH.read_text(encoding="utf-8"))
    assert output["result"]["verification"] == {"total_fraction": "1", "is_consistent": True}
    assert output["result"]["post_tasil"]["total_shares"] == 120
    distribution = output["result"]["post_tasil"]["distribution"]
    assert [item["per_head_shares"] for item in distribution] == ["15/120", "20/120", "34/120", "17/120"]
    assert sum(Fraction(item["per_head_shares"]) * item["count"] for item in distribution) == 1
    assert post.call_count == 2
    for call in post.call_args_list:
        payload = call.kwargs["json"]
        assert payload["think"] is False
        assert payload["options"]["temperature"] == 0
    prompt = post.call_args_list[1].kwargs["json"]["prompt"]
    assert json.dumps(PARSED, ensure_ascii=False) in prompt
    assert json.dumps(output["sources"], ensure_ascii=False) in prompt


def test_retriever_matches_whole_relations_and_is_independent_of_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert len(retrieve_rules(PARSED)) == 3
    assert retrieve_rules({"mentioned_relatives": []}) == []
    assert retrieve_rules({"mentioned_relatives": [{"relation": "بنت ابن", "count": 1}]}) == []
    assert retrieve_rules({"mentioned_relatives": [{"relation": "زوجة", "count": 0}]}) == []


def test_fraction_verifier_flags_inconsistent_model_output():
    result = model_result()
    result["post_tasil"]["distribution"][2]["per_head_shares"] = "1/3"
    with patch("requests.post", return_value=response_for(result)):
        output = analyze_case(QUESTION, PARSED, retrieve_rules(PARSED))
    assert output["verification"]["is_consistent"] is False
    assert output["verification"]["total_fraction"] != "1"


def test_reasoner_rejects_invalid_json():
    response = Mock()
    response.json.return_value = {"response": "invalid JSON"}
    with patch("requests.post", return_value=response), pytest.raises(ValueError, match="invalid JSON"):
        analyze_case(QUESTION, PARSED, retrieve_rules(PARSED))
