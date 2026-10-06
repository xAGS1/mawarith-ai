"""Small exact residuary strategy; rule selection stays source-backed."""
from dataclasses import dataclass
from fractions import Fraction
import json
import hashlib
from pathlib import Path


def solver_source_ids(group: str) -> list[str]:
    data = json.loads(Path(__file__).with_name("solver_sources.json").read_text(encoding="utf-8"))
    ids = data[group]
    if not ids or any(i not in data["passages"] for i in ids):
        raise ValueError("Missing approved solver evidence")
    for source_id in ids:
        passage = data["passages"][source_id]
        if (not passage["provenance"].get("verified_source")
                or hashlib.sha256(passage["exact_text"].encode("utf-8")).hexdigest() != passage["text_sha256"]):
            raise ValueError("Invalid solver evidence integrity")
    return ids


@dataclass(frozen=True)
class ResiduaryFamily:
    family_id: str
    priority: int
    weights: dict[str, int]

    def distribute(self, counts: dict[str, int], residue: Fraction) -> dict[str, Fraction]:
        if not isinstance(residue, Fraction) or not 0 <= residue <= 1:
            raise ValueError("Residue must be an exact nonnegative fraction")
        if not counts or any(type(n) is not int or n <= 0 for n in counts.values()):
            raise ValueError("Invalid residuary counts")
        if any(r not in self.weights or type(self.weights[r]) is not int or self.weights[r] <= 0 for r in counts):
            raise ValueError("Unsupported residuary member or weight")
        units = sum(counts[r] * self.weights[r] for r in counts)
        return {r: residue * self.weights[r] / units for r in counts}


def include_children_rule(parsed: dict, rules: list[dict]) -> list[dict]:
    from backend.rules.case_features import build_case_features
    features = build_case_features(parsed)
    if not features["has_son"] or features["has_daughter"]:
        return rules
    if any(r["result"].get("allocation") == "residue" and "ابن" in r["applies_to"] for r in rules):
        return rules
    ids = solver_source_ids("sons_residuary")
    return [*rules, {
        "rule_id": "children_residuary_equal_males", "applies_to": ["ابن"],
        "conditions": {"has_son": True, "has_daughter": False},
        "result": {"allocation": "residue", "male_weight": 1, "female_weight": 1},
        "topic": "تعصيب الأبناء", "rule": "يقسم الباقي بين الأبناء بالتساوي.",
        "source_ids": ids,
        "source": {"source_type": "fiqh", "source_name": "الموسوعة الفقهية الكويتية", "source_id": ids[0]},
    }]


def select_solver_rules(parsed: dict) -> list[dict]:
    from backend.rag.retriever import retrieve_rules
    from backend.rules.case_features import build_case_features
    features = build_case_features(parsed)
    normalized = {"mentioned_relatives": [{"relation": r, "count": n} for r, n in features["relations"].items()]}
    return include_children_rule(normalized, retrieve_rules(normalized, features))


def select_family(candidates: list[tuple[dict, dict[str, int]]]) -> tuple[ResiduaryFamily, dict, dict[str, int]] | None:
    from backend.rules.safety import SolverReferral
    if not candidates:
        return None
    # Priority cannot justify silently discarding a competing class.
    if len(candidates) != 1:
        raise SolverReferral("unsupported_competing_residuaries")
    rule, counts = candidates[0]
    result = rule["result"]
    children = set(counts) <= {"ابن", "بنت"} and "ابن" in counts
    legacy_siblings = set(counts) == {"أخ شقيق", "أخت شقيقة"} and rule["rule_id"] == "full_brothers_and_sisters_kalalah"
    if not (children or legacy_siblings):
        raise SolverReferral("unsupported_residuary_family")
    expected_id = "sons_and_daughters" if "بنت" in counts else "children_residuary_equal_males"
    if children and (rule["rule_id"] != expected_id
                     or set(rule["applies_to"]) != set(counts)
                     or result["male_weight"] != (2 if "بنت" in counts else 1)
                     or result["female_weight"] != 1):
        raise SolverReferral("unsupported_children_strategy")
    if children and "بنت" not in counts and rule.get("source_ids", []) != solver_source_ids("sons_residuary"):
        raise SolverReferral("unsupported_children_source")
    weights = {r: result["female_weight"] if r.startswith(("بنت", "أخت")) else result["male_weight"] for r in counts}
    return ResiduaryFamily("direct_children" if children else "existing_full_siblings", 10 if children else 30, weights), rule, counts
