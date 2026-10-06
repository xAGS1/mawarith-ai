"""Derive facts from canonical relatives without deciding inheritance rulings."""


SIBLING_RELATIONS = frozenset({
    "أخ شقيق", "أخت شقيقة", "أخ لأب", "أخت لأب", "أخ لأم", "أخت لأم",
    "أخ", "أخت",
})

COUNT_RELATIONS = {
    "husband_count": "زوج", "wife_count": "زوجة",
    "son_count": "ابن", "daughter_count": "بنت",
    "father_count": "أب", "mother_count": "أم",
    "full_brother_count": "أخ شقيق", "full_sister_count": "أخت شقيقة",
    "maternal_brother_count": "أخ لأم", "maternal_sister_count": "أخت لأم",
}


def build_case_features(parsed_relations: dict) -> dict:
    from backend.rules.population import normalized_counts, descendant_direction
    relations = normalized_counts(parsed_relations)

    # The spouse rules mean an inheriting descendant through sons, not every
    # biological descendant. Presence itself is retained independently.
    descendants = {
        relation for relation in relations
        if descendant_direction(relation) == "inheriting"
    }
    return {
        "relations": relations,
        "present_in_case": dict(relations),
        "has_heir_descendant": bool(descendants),
        "has_biological_descendant": any(descendant_direction(r) for r in relations),
        "has_descendant": bool(descendants),
        "has_male_descendant": any(r.split()[0] == "ابن" for r in descendants),
        "has_female_descendant": any(r.split()[0] == "بنت" for r in descendants),
        "has_child": bool({"ابن", "بنت"}.intersection(relations)),
        "has_son": "ابن" in relations,
        "has_daughter": "بنت" in relations,
        "has_spouse": bool({"زوج", "زوجة"}.intersection(relations)),
        "has_father": "أب" in relations,
        "has_mother": "أم" in relations,
        "sibling_count": sum(relations.get(r, 0) for r in SIBLING_RELATIONS),
        "has_kalalah_context": not descendants and "أب" not in relations,
        **{feature: relations.get(relation, 0) for feature, relation in COUNT_RELATIONS.items()},
    }
