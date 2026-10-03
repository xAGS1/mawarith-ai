import copy
import json
from unittest.mock import patch

import pytest

from backend.rag.coverage import check_source_coverage
from backend.rag.retriever import RULES_PATH, conditions_satisfied, retrieve_rules
from backend.rag.source_validation import validate_rule_records
from backend.rules.case_features import build_case_features


def case(*relatives):
    return {"mentioned_relatives": [{"relation": r, "count": c} for r, c in relatives]}


@pytest.mark.parametrize("relatives,rule_id,fraction", [
    ([("زوجة", 1), ("ابن", 2)], "wife_with_descendant", "1/8"),
    ([("زوجة", 1), ("أخ شقيق", 1)], "wife_without_descendant", "1/4"),
    ([("زوج", 1), ("بنت", 1)], "husband_with_descendant", "1/4"),
    ([("زوج", 1)], "husband_without_descendant", "1/2"),
    ([("بنت", 1)], "one_daughter_without_son", "1/2"),
    ([("بنت", 2)], "multiple_daughters_without_son", "2/3"),
    ([("أم", 1), ("ابن", 1)], "mother_with_child", "1/6"),
    ([("أم", 1)], "mother_no_child_no_siblings", "1/3"),
    ([("أم", 1), ("أخ شقيق", 2)], "mother_with_siblings", "1/6"),
    ([("أب", 1), ("ابن", 1)], "father_with_child", "1/6"),
    ([("أخت شقيقة", 1)], "one_full_sister_kalalah", "1/2"),
    ([("أخت شقيقة", 2)], "multiple_full_sisters_kalalah", "2/3"),
])
def test_requested_fixed_share_rules(relatives, rule_id, fraction):
    parsed = case(*relatives)
    rules = retrieve_rules(parsed, build_case_features(parsed))
    matching = next(r for r in rules if r["rule_id"] == rule_id)
    assert matching["result"]["fraction"] == fraction
    if rule_id.startswith("wife_"):
        assert len([r for r in rules if "زوجة" in r["applies_to"]]) == 1


@pytest.mark.parametrize("relatives,rule_id", [
    ([("ابن", 1), ("بنت", 1)], "sons_and_daughters"),
    ([("أخ شقيق", 1), ("أخت شقيقة", 1)], "full_brothers_and_sisters_kalalah"),
])
def test_joint_allocation(relatives, rule_id):
    parsed = case(*relatives)
    rule = next(r for r in retrieve_rules(parsed, build_case_features(parsed)) if r["rule_id"] == rule_id)
    assert rule["result"] == {"allocation": "residue", "male_weight": 2, "female_weight": 1}


@pytest.mark.parametrize("extra", [[("أب", 1)], [("ابن", 1)], [("بنت", 1)], [("بنت ابن", 1)]])
def test_kalalah_requires_no_descendant_and_no_father(extra):
    parsed = case(("أخت شقيقة", 1), *extra)
    features = build_case_features(parsed)
    assert features["has_kalalah_context"] is False
    assert not any(r["rule_id"].endswith("kalalah") for r in retrieve_rules(parsed, features))


def test_all_counts_and_duplicate_relatives():
    parsed = case(("زوج", 1), ("زوجة", 2), ("ابن", 2), ("ابن", 1), ("بنت", 4),
                  ("أب", 1), ("أم", 1), ("أخ شقيق", 3), ("أخت شقيقة", 2), ("أخ لأم", 2), ("أخت لأم", 1))
    features = build_case_features(parsed)
    assert {k: features[k] for k in ["husband_count", "wife_count", "son_count", "daughter_count", "father_count", "mother_count", "full_brother_count", "full_sister_count", "maternal_brother_count", "maternal_sister_count"]} == {
        "husband_count": 1, "wife_count": 2, "son_count": 3, "daughter_count": 4,
        "father_count": 1, "mother_count": 1, "full_brother_count": 3, "full_sister_count": 2,
        "maternal_brother_count": 2, "maternal_sister_count": 1,
    }
    assert features["sibling_count"] == 8


@pytest.mark.parametrize("conditions,features,expected", [
    ({"n_gte": 2}, {"n": 2}, True), ({"n_gte": 2}, {"n": 1}, False),
    ({"n_lte": 2}, {"n": 2}, True), ({"n_lte": 2}, {"n": 3}, False),
    ({"n_gte": 1, "n_lte": 3}, {"n": 2}, True),
    ({"n_gte": 1}, {"n": True}, False), ({"n_lte": True}, {"n": 1}, False),
    ({"n_gte": 2}, {}, False),
])
def test_generic_suffix_comparisons(conditions, features, expected):
    assert conditions_satisfied(conditions, features) is expected


def test_coverage_rechecks_conditions_even_with_unfiltered_rules():
    records = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    brother = case(("زوجة", 1), ("أخ شقيق", 1))
    assert check_source_coverage(brother, records)["unsupported_relations"] == ["أخ شقيق"]
    sister_with_father = case(("أخت شقيقة", 1), ("أب", 1))
    assert check_source_coverage(sister_with_father, records)["covered_relations"] == []
    wife = case(("زوجة", 1))
    wrong_rule = [r for r in records if r["rule_id"] == "wife_with_descendant"]
    assert check_source_coverage(wife, wrong_rule)["is_sufficient"] is False


def test_entire_source_batch_validates():
    records = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    assert validate_rule_records(records) is records
    assert len(records) == 14
    assert {r["source"]["reference"] for r in records} == {"4:11", "4:12", "4:176"}


@pytest.mark.parametrize("missing", ["rule_id", "applies_to", "conditions", "result", "topic", "rule", "source"])
def test_validator_rejects_missing_rule_fields(missing):
    record = json.loads(RULES_PATH.read_text(encoding="utf-8"))[0]
    del record[missing]
    with pytest.raises(ValueError):
        validate_rule_records([record])


@pytest.mark.parametrize("field", ["source_type", "source_name", "reference"])
def test_validator_rejects_missing_source_fields(field):
    record = json.loads(RULES_PATH.read_text(encoding="utf-8"))[0]
    del record["source"][field]
    with pytest.raises(ValueError):
        validate_rule_records([record])


@pytest.mark.parametrize("change", [
    {"source": {"source_type": "quran", "source_name": "القرآن الكريم", "reference": "4:10"}},
    {"conditions": {"daughter_count_gte": True}},
    {"result": {"fraction": "1/0"}},
    {"applies_to": []},
])
def test_invalid_source_records_block_loading(change):
    record = json.loads(RULES_PATH.read_text(encoding="utf-8"))[0]
    record.update(change)
    with patch("backend.rag.retriever.json.load", return_value=[record]), pytest.raises(ValueError):
        retrieve_rules(case(("زوج", 1)), build_case_features(case(("زوج", 1))))


def test_duplicate_rule_ids_rejected():
    record = json.loads(RULES_PATH.read_text(encoding="utf-8"))[0]
    with pytest.raises(ValueError):
        validate_rule_records([record, copy.deepcopy(record)])
