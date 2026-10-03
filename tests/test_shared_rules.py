import ast
from pathlib import Path

import pytest

from backend.rag.retriever import conditions_satisfied, retrieve_rules
from backend.rules.case_features import build_case_features
from backend.verifier.fractions import verify_and_normalize


def parsed(*relatives):
    return {"mentioned_relatives": [{"relation": r, "count": c} for r, c in relatives]}


def test_case_a_features_and_condition_matched_rules():
    case = parsed(("زوجة", 1), ("أم", 1), ("ابن", 2), ("بنت", 1))
    features = build_case_features(case)
    assert features["relations"] == {"زوجة": 1, "أم": 1, "ابن": 2, "بنت": 1}
    assert features["has_descendant"] is True
    assert features["has_male_descendant"] is True
    assert features["has_female_descendant"] is True
    assert features["has_spouse"] is True
    assert features["has_mother"] is True
    assert features["has_father"] is False
    assert features["sibling_count"] == 0
    rules = retrieve_rules(case, features)
    assert {r["rule_id"] for r in rules} == {"wife_with_descendant", "mother_with_child", "sons_and_daughters"}
    assert next(r for r in rules if r["rule_id"] == "wife_with_descendant")["result"]["fraction"] == "1/8"


def test_case_b_wife_and_full_brother():
    # Parsed form of مات وترك زوجة وأخا شقيقا.
    case = parsed(("زوجة", 1), ("أخ شقيق", 1))
    features = build_case_features(case)
    assert features["has_descendant"] is False
    assert features["sibling_count"] == 1
    rules = retrieve_rules(case, features)
    assert [r["rule_id"] for r in rules] == ["wife_without_descendant"]
    assert rules[0]["result"]["fraction"] == "1/4"
    assert rules[0]["source"] == {"source_type": "quran", "source_name": "القرآن الكريم", "reference": "4:12"}


def test_descendants_are_not_nephews_or_cousins_and_duplicates_merge():
    features = build_case_features(parsed(("ابن أخ شقيق", 3), ("ابن عم", 2)))
    assert features["has_descendant"] is False
    assert features["sibling_count"] == 0
    features = build_case_features(parsed(("بنت ابن", 2), ("بنت ابن", 1)))
    assert features["relations"]["بنت ابن"] == 3
    assert features["has_descendant"] is True
    assert features["has_female_descendant"] is True
    assert features["has_child"] is False


@pytest.mark.parametrize("conditions,features,expected", [
    ({"flag": True}, {"flag": True}, True),
    ({"flag": False}, {"flag": True}, False),
    ({"count": 2}, {"count": 2}, True),
    ({"count": 2}, {"count": 3}, False),
    ({"count": {"min": 2, "max": 4}}, {"count": 2}, True),
    ({"count": {"min": 2, "max": 4}}, {"count": 4}, True),
    ({"count": {"min": 2, "max": 4}}, {"count": 5}, False),
    ({"count": {"eq": 2}}, {"count": 2}, True),
    ({"flag": True}, {"flag": 1}, False),
    ({"count": 1}, {"count": True}, False),
    ({"flag": False}, {}, False),
    ({"count": {"min": 1}}, {"count": True}, False),
    ({"count": {"unknown": 1}}, {"count": 2}, False),
])
def test_generic_condition_evaluator(conditions, features, expected):
    assert conditions_satisfied(conditions, features) is expected


def test_single_daughter_does_not_retrieve_joint_children_rule():
    case = parsed(("بنت", 1))
    assert [r["rule_id"] for r in retrieve_rules(case, build_case_features(case))] == ["one_daughter_without_son"]


def test_verifier_rebuilds_group_shares_without_mutating_model_result():
    raw = {"shares": [{"heir": "ابن", "count": 2, "fraction": "17/60"}],
           "post_tasil": {"distribution": [{"heir": "ابن", "count": 2, "per_head_shares": "17/60"}]}}
    result = verify_and_normalize(raw)
    assert result["shares"][0]["fraction"] == "17/30"
    assert raw["shares"][0]["fraction"] == "17/60"
    assert result["verification"] == {"total_fraction": "17/30", "is_consistent": False}
    assert verify_and_normalize({})["verification"]["is_consistent"] is False


@pytest.mark.parametrize("count,fraction", [(True, "1/2"), (0, "1/2"), (-1, "1/2"), (1, "-1/2"), (1, "2")])
def test_verifier_rejects_invalid_distribution(count, fraction):
    with pytest.raises(ValueError):
        verify_and_normalize({"post_tasil": {"distribution": [{"heir": "ابن", "count": count, "per_head_shares": fraction}]}})


def test_shared_modules_do_not_import_qwen():
    root = Path(__file__).resolve().parents[1] / "backend"
    for directory in ("rules", "rag", "verifier", "schemas"):
        for path in (root / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    assert "qwen" not in (node.module or "").lower()
                elif isinstance(node, ast.Import):
                    assert all("qwen" not in alias.name.lower() for alias in node.names)
