"""Normalize presence separately from source-backed share eligibility."""
from dataclasses import dataclass


def canonical_relation(relation: str) -> str:
    relation = relation.strip()
    english = relation.lower()
    words = {"son": "ابن", "daughter": "بنت"}
    tokens = english.split("_of_")
    if all(t in words for t in tokens):
        return " ".join(words[t] for t in tokens)
    tokens = english.replace("'s ", " ").split()
    if "'s " in english and all(t in words for t in tokens):
        return " ".join(words[t] for t in reversed(tokens))
    return " ".join(relation.split())


def normalized_counts(parsed: dict) -> dict[str, int]:
    counts = {}
    for item in parsed.get("mentioned_relatives", []):
        relation = canonical_relation(item["relation"])
        count = item["count"]
        if not relation or type(count) is not int or count < 0:
            raise ValueError("Relatives require a nonempty relation and a nonnegative integer count")
        if count:
            counts[relation] = counts.get(relation, 0) + count
    return counts


def descendant_direction(relation: str) -> str | None:
    tokens = relation.split()
    if not tokens or not set(tokens) <= {"ابن", "بنت"}:
        return None
    return "inheriting" if all(t == "ابن" for t in tokens[1:]) else "matrilineal"


@dataclass(frozen=True)
class CasePopulation:
    """Eligible means not excluded here; complete rule coverage is still required."""
    present_in_case: dict[str, int]
    eligible_to_inherit: dict[str, int]
    excluded_by_another_heir: dict[str, dict]


def prepare_case(parsed: dict) -> CasePopulation:
    present = normalized_counts(parsed)
    eligible = dict(present)
    excluded = {}
    # Only the locally sourced son -> son's son exclusion is executable here.
    # No sibling, granddaughter or impediment policy is inferred.
    if "ابن" in present:
        from backend.rules.residuaries import solver_source_ids
        for relation in present:
            if len(relation.split()) > 1 and set(relation.split()) == {"ابن"}:
                excluded[relation] = {
                    "rule_id": "son_excludes_agnatic_grandsons", "excluded_by": "ابن",
                    "source_ids": solver_source_ids("son_exclusion"),
                }
                eligible.pop(relation)
    return CasePopulation(present, eligible, excluded)
