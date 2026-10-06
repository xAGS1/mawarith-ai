"""Exact fixed shares followed by one source-backed residuary family."""
from fractions import Fraction
from backend.rules.case_features import build_case_features
from backend.rag.retriever import conditions_satisfied
from backend.rules.population import prepare_case
from backend.rules.residuaries import select_family
from backend.rules.safety import SolverReferral, unsupported_case_reason
from backend.verifier.fractions import verify_and_normalize


def source_ids(rule):
    if rule.get("source_ids"):
        return list(rule["source_ids"])
    source = rule.get("source", {})
    if source.get("source_type") == "quran" and source.get("reference"):
        return ["quran:" + source["reference"]]
    return [source["source_id"]] if source.get("source_id") else []


def allocate(parsed, rules):
    unsupported = unsupported_case_reason(parsed)
    if unsupported:
        raise SolverReferral(unsupported)
    features = build_case_features(parsed)
    population = prepare_case(parsed)
    counts = population.eligible_to_inherit
    groups, residue, trace = {}, [], []
    for rule in rules:
        if not conditions_satisfied(rule.get("conditions", {}), features):
            raise SolverReferral("inapplicable_selected_rule")
        relations = [r for r in rule["applies_to"] if r in counts]
        result = rule["result"]
        if "fraction" in result:
            if len(relations) != 1 or relations[0] in groups or not isinstance(result["fraction"], (str, Fraction)):
                raise SolverReferral("overlapping_or_invalid_fixed_share")
            groups[relations[0]] = Fraction(result["fraction"])
            if not 0 < groups[relations[0]] <= 1:
                raise SolverReferral("invalid_fixed_share")
            trace.append({"rule_id": rule["rule_id"], "category": "fixed_share", "heirs_affected": relations,
                          "group_fractions": {relations[0]: str(groups[relations[0]])},
                          "per_head_fractions": {relations[0]: str(groups[relations[0]] / counts[relations[0]])},
                          "source_ids": source_ids(rule)})
        elif result.get("allocation") == "residue":
            residue.append((rule, {r: counts[r] for r in relations}))
        else:
            raise SolverReferral("unsupported_executable_allocation")
    remainder = Fraction(1) - sum(groups.values(), Fraction())
    if remainder < 0:
        raise SolverReferral("unsupported_awl")
    selected = select_family(residue)
    if selected:
        family, rule, members = selected
        if any(r in groups for r in members):
            raise SolverReferral("overlapping_residuary_rules")
        individual = family.distribute(members, remainder)
        groups.update({r: individual[r] * members[r] for r in members})
        trace.append({"rule_id": ("children_residuary_mixed_2_to_1" if "بنت" in members else "children_residuary_equal_males")
                      if family.family_id == "direct_children" else rule["rule_id"],
                      "source_rule_id": rule["rule_id"], "category": "residuary",
                      "family_id": family.family_id, "priority": family.priority,
                      "heirs_affected": list(members), "input_residue": str(remainder),
                      "per_head_fractions": {r: str(f) for r, f in individual.items()},
                      "source_ids": source_ids(rule)})
    if set(groups) != set(counts):
        raise SolverReferral("unsupported_heir_or_residuary")
    for relation, exclusion in population.excluded_by_another_heir.items():
        groups[relation] = Fraction()
        trace.append({**exclusion, "category": "exclusion", "heirs_affected": [relation], "per_head_fractions": {relation: "0"}})
    result = verify_and_normalize({"heirs": [{"heir": r, "count": n} for r, n in population.present_in_case.items()],
        "blocked": [{"heir": r, "count": population.present_in_case[r]} for r in population.excluded_by_another_heir],
        "rule_trace": trace, "awl_or_radd": "none", "post_tasil": {"distribution": [
            {"heir": r, "count": population.present_in_case[r], "per_head_shares": str(f / population.present_in_case[r])} for r, f in groups.items()]}})
    if not result["verification"]["is_consistent"]:
        raise SolverReferral("unsupported_remainder_no_automatic_radd")
    return result
