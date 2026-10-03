"""Deterministic relation coverage using only retrieved rule metadata."""

from backend.rag.retriever import conditions_satisfied
from backend.rules.case_features import build_case_features


def check_source_coverage(parsed_relations: dict, retrieved_rules: list) -> dict:
    """Check exact applies_to names and independently re-evaluate conditions.

    Preserve parser order and do not count duplicates or individual head counts
    more than once. An empty case fails closed. This checks source availability,
    not completeness or legal correctness of the retrieved rulings.
    """
    relations = list(dict.fromkeys(
        item["relation"].strip()
        for item in parsed_relations.get("mentioned_relatives", [])
    ))
    features = build_case_features(parsed_relations)
    supported = {
        relation.strip()
        for rule in retrieved_rules
        if isinstance(rule.get("conditions"), dict)
        and conditions_satisfied(rule["conditions"], features)
        for relation in rule.get("applies_to", [])
    }
    covered = [relation for relation in relations if relation and relation in supported]
    unsupported = [relation for relation in relations if not relation or relation not in supported]
    return {
        "is_sufficient": bool(relations) and not unsupported,
        "covered_relations": covered,
        "unsupported_relations": unsupported,
        "coverage_ratio": len(covered) / len(relations) if relations else 0.0,
    }
