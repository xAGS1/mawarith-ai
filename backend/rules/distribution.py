"""Allocate only executable rule results, using exact rational arithmetic."""
from fractions import Fraction
from backend.rules.case_features import build_case_features
from backend.verifier.fractions import verify_and_normalize


def allocate(parsed, rules):
    counts = build_case_features(parsed)["relations"]
    groups, residue = {}, []
    for rule in rules:
        relations = [r for r in rule["applies_to"] if r in counts]
        result = rule["result"]
        if "fraction" in result:
            if len(relations) != 1 or relations[0] in groups:
                raise ValueError("Overlapping or unsupported fixed-share rule")
            groups[relations[0]] = Fraction(result["fraction"])
        elif result.get("allocation") == "residue":
            residue.append((relations, result))
        else:
            raise ValueError("Unsupported executable allocation")
    remainder = 1 - sum(groups.values(), Fraction())
    if remainder < 0 or len(residue) > 1:
        raise ValueError("No supported complete allocation")
    if residue:
        relations, result = residue[0]
        if any(r in groups for r in relations):
            raise ValueError("Overlapping residue rule")
        # Weight values come only from the applied structured rule.
        weights = {r: result["female_weight"] if r.startswith(("بنت", "أخت")) else result["male_weight"] for r in relations}
        units = sum(counts[r] * weights[r] for r in relations)
        if units <= 0:
            raise ValueError("Empty residue group")
        groups.update({r: remainder * counts[r] * weights[r] / units for r in relations})
    if set(groups) != set(counts):
        raise ValueError("No rule-backed share for every stated heir")
    result = verify_and_normalize({"heirs": [{"heir": r, "count": n} for r, n in counts.items()],
        "blocked": [], "awl_or_radd": "none", "post_tasil": {"distribution": [
            {"heir": r, "count": counts[r], "per_head_shares": str(f / counts[r])} for r, f in groups.items()]}})
    if not result["verification"]["is_consistent"]:
        raise ValueError("Unsupported remainder; no automatic awl or radd")
    return result
