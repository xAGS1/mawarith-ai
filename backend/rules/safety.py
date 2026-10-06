"""Named capability guards, independent of arithmetic consistency."""
from backend.rules.case_features import build_case_features, SIBLING_RELATIONS
from backend.rules.population import descendant_direction


class SolverReferral(ValueError):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def unsupported_case_reason(parsed: dict) -> str | None:
    features = build_case_features(parsed)
    relations = set(features["relations"])
    if any(descendant_direction(r) == "matrilineal" for r in relations):
        return "unsupported_matrilineal_descendant"
    if relations in ({"زوج", "أب", "أم"}, {"زوجة", "أب", "أم"}):
        return "unsupported_umariyyat"
    if relations.intersection(SIBLING_RELATIONS) and (features["has_father"] or features["has_heir_descendant"]):
        return "unsupported_sibling_exclusion_policy"
    if any(parsed.get(k) for k in ("barred_by_external_impediment", "impediments")) or any(
        item.get("barred_by_external_impediment") or item.get("impediment")
        for item in parsed.get("mentioned_relatives", [])
    ):
        return "unsupported_external_impediment_policy"
    if features["father_count"] > 1 or features["mother_count"] > 1 or features["husband_count"] > 1 or ({"زوج", "زوجة"} <= relations):
        return "unsupported_relationship_counts"
    return None
