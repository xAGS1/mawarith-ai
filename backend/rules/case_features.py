"""Derive facts from canonical relatives without deciding inheritance rulings."""


SIBLING_RELATIONS = frozenset({
    "أخ شقيق", "أخت شقيقة", "أخ لأب", "أخت لأب", "أخ لأم", "أخت لأم",
    "أخ", "أخت",
})


def build_case_features(parsed_relations: dict) -> dict:
    relations = {}
    for item in parsed_relations.get("mentioned_relatives", []):
        relation = item["relation"].strip()
        count = item["count"]
        if not relation or type(count) is not int or count < 0:
            raise ValueError("Relatives require a nonempty relation and a nonnegative integer count")
        if count:
            relations[relation] = relations.get(relation, 0) + count

    # A chain containing only child relations is a factual descendant.
    # This includes بنت ابن but excludes ابن أخ and ابن عم.
    descendants = {
        relation for relation in relations
        if set(relation.split()) <= {"ابن", "بنت"}
    }
    return {
        "relations": relations,
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
    }
