"""Retrieve local rules by exact relation names, preserving source metadata."""

import json
from pathlib import Path

from backend.rag.source_validation import validate_rule_records


RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "sources" / "inheritance_rules.json"


def conditions_satisfied(conditions: dict, case_features: dict) -> bool:
    """Match equality, *_gte/*_lte, or integer {eq, min, max} constraints.

    Missing facts, type mismatches and unsupported operators never match.
    Python's bool/int equivalence is deliberately excluded.
    """
    for feature, expected in conditions.items():
        comparison = None
        if feature.endswith(("_gte", "_lte")):
            feature, comparison = feature.rsplit("_", 1)
        if feature not in case_features:
            return False
        actual = case_features[feature]
        if comparison is not None:
            if type(actual) is not int or type(expected) is not int:
                return False
            if comparison == "gte" and actual < expected:
                return False
            if comparison == "lte" and actual > expected:
                return False
        elif isinstance(expected, dict):
            if not expected or type(actual) is not int:
                return False
            for operator, limit in expected.items():
                if type(limit) is not int:
                    return False
                if operator == "eq":
                    matched = actual == limit
                elif operator == "min":
                    matched = actual >= limit
                elif operator == "max":
                    matched = actual <= limit
                else:
                    return False
                if not matched:
                    return False
        elif type(expected) not in (bool, int) or type(actual) is not type(expected) or actual != expected:
            return False
    return True


def retrieve_rules(parsed_relations: dict, case_features: dict) -> list:
    """Return only rules with matching relatives and satisfied conditions.

    Match whole relation names so, for example, بنت ابن does not match بنت.
    Resolve the source file relative to the project, independent of the cwd.
    """
    relations = {
        item["relation"].strip()
        for item in parsed_relations.get("mentioned_relatives", [])
        if item["count"] > 0
    }
    with RULES_PATH.open(encoding="utf-8") as source_file:
        rules = validate_rule_records(json.load(source_file))

    return [
        rule for rule in rules
        if relations.intersection(rule["applies_to"])
        and conditions_satisfied(rule["conditions"], case_features)
    ]
