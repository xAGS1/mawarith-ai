"""Small educational catalogs, without model calls or calculated distributions."""
from copy import deepcopy

from backend.rag.coverage import check_source_coverage
from backend.rag.fiqh.vector_store import load_chunks
from backend.rag.retriever import retrieve_rules
from backend.rules.case_features import build_case_features
from backend.rules.educational_concepts import supported_concepts


def bilingual(ar: str, en: str) -> dict:
    return {"ar": ar, "en": en}


# Only concepts already defined by the source-bound metadata can have a definition.
_CARDS = (
    ("fixed_share_heirs", "أصحاب الفروض", "Fixed-share heirs", None,
     ("fixed_share", "blocking")),
    ("fixed_share", "الفرض", "Fixed share", "الفرض",
     ("fixed_share_heirs", "residuary_inheritance", "awl", "radd")),
    ("residuary_heirs", "العصبة", "Residuary heirs", "العصبة",
     ("residuary_inheritance", "fixed_share_heirs")),
    ("residuary_inheritance", "التعصيب", "Residuary inheritance", "التعصيب",
     ("residuary_heirs", "fixed_share")),
    ("blocking", "الحجب", "Blocking", None,
     ("fixed_share_heirs", "residuary_heirs")),
    ("awl", "العول", "Awl", None, ("fixed_share", "radd")),
    ("radd", "الرد", "Radd", None, ("fixed_share", "awl")),
)


def list_concepts() -> list[dict]:
    """Bind existing definitions to validated local evidence, without live RAG.

    Missing or invalid evidence produces limited cards, never guessed definitions.
    Source dictionaries retain the original provenance; definitions are summaries,
    not immutable quotations of religious text.
    """
    try:
        chunks = load_chunks()
    except (ValueError, OSError):
        chunks = []
    evidence = [{"evidence_id": c["chunk_id"], "text": c["text"]} for c in chunks]
    by_id = {c["chunk_id"]: c for c in chunks}
    cards = []
    for concept_id, ar, en, query, related in _CARDS:
        definitions, sources = None, []
        if query:
            matches = {language: supported_concepts(query, language, evidence)
                       for language in ("ar", "en")}
            if all(matches.values()):
                definitions = {language: matches[language][0]["explanation"]
                               for language in ("ar", "en")}
                chunk = by_id[matches["ar"][0]["evidence_id"]]
                sources = [{k: v for k, v in chunk.items() if k != "text"}]
        cards.append({"concept_id": concept_id, "title_ar": ar, "title_en": en,
            "short_definition": definitions,
            "learn_question": bilingual(f"ما معنى {ar} في المواريث؟", f"What does {en.lower()} mean in Islamic inheritance?"),
            "difficulty": "introductory" if concept_id not in {"awl", "radd"} else "intermediate",
            "related_concepts": list(related),
            "availability": "available" if definitions else "limited", "sources": sources})
    return cards


_EXAMPLES = (
    {"example_id": "wife_mother_children", "title_ar": "زوجة وأم وأبناء وبنت",
     "title_en": "Wife, mother, sons and daughter",
     "scenario_ar": "مات وترك زوجة وأما وابنين وبنت فقط. ما نصيب كل وارث؟",
     "scenario_en": "A man died leaving only one wife, his mother, two sons and one daughter. What is each heir's share?",
     "learning_objective_ar": "تعرّف كيف تجتمع الفروض مع توزيع الباقي في مثال بسيط.",
     "learning_objective_en": "Explore fixed shares and distribution of the residue in a simple example.",
     "concepts": ["fixed_share", "fixed_share_heirs", "residuary_heirs", "residuary_inheritance"],
     "relatives": [("زوجة", 1), ("أم", 1), ("ابن", 2), ("بنت", 1)]},
    {"example_id": "wife_son_daughter", "title_ar": "زوجة وابن وبنت",
     "title_en": "Wife, son and daughter",
     "scenario_ar": "مات وترك زوجة وابنا وبنتا فقط. ما نصيب كل وارث؟",
     "scenario_en": "A man died leaving only one wife, one son and one daughter. What is each heir's share?",
     "learning_objective_ar": "استكشف أثر وجود الأبناء في القاعدة المطبقة على الزوجة.",
     "learning_objective_en": "Explore which wife rule applies when children are present.",
     "concepts": ["fixed_share", "residuary_inheritance"],
     "relatives": [("زوجة", 1), ("ابن", 1), ("بنت", 1)]},
    {"example_id": "mother_son_daughters", "title_ar": "أم وابن وبنتان",
     "title_en": "Mother, son and two daughters",
     "scenario_ar": "مات وترك أما وابنا وبنتين فقط. ما نصيب كل وارث؟",
     "scenario_en": "A person died leaving only their mother, one son and two daughters. What is each heir's share?",
     "learning_objective_ar": "استكشف الفرق بين نصيب المجموعة ونصيب كل فرد.",
     "learning_objective_en": "Explore the difference between a group's share and each individual's share.",
     "concepts": ["fixed_share", "residuary_heirs", "residuary_inheritance"],
     "relatives": [("أم", 1), ("ابن", 1), ("بنت", 2)]},
)


def list_examples() -> list[dict]:
    examples = []
    for item in _EXAMPLES:
        example = deepcopy(item)
        parsed = {"mentioned_relatives": [{"relation": relation, "count": count}
                  for relation, count in example.pop("relatives")]}
        try:
            rules = retrieve_rules(parsed, build_case_features(parsed))
            supported = check_source_coverage(parsed, rules)["is_sufficient"]
        except (ValueError, OSError):
            supported = False
        example["case_supported"] = supported
        examples.append(example)
    return examples


def list_paths() -> list[dict]:
    steps = [
        ("overview", [], "ما هو نظام المواريث في الإسلام؟", "What is Islamic inheritance?"),
        ("fixed_shares", ["fixed_share"], "ما معنى الفرض؟", "What is a fixed share?"),
        ("fixed_share_heirs", ["fixed_share_heirs"], "ما معنى أصحاب الفروض؟", "What is a fixed-share heir?"),
        ("residuary_heirs", ["residuary_heirs", "residuary_inheritance"], "ما معنى العصبة؟", "What is a residuary heir?"),
        ("blocking", ["blocking"], "ما معنى الحجب في المواريث؟", "What is blocking in Islamic inheritance?"),
        ("rule_interaction", ["fixed_share", "residuary_inheritance"], "ما الفرق بين الفرض والتعصيب؟", "What is the difference between a fixed share and residuary inheritance?"),
    ]
    path_steps = [{"step_id": step_id, "concepts": concepts, "mode": "learn",
                   "question": bilingual(ar, en)} for step_id, concepts, ar, en in steps]
    example = _EXAMPLES[0]
    path_steps.append({"step_id": "simple_example", "concepts": list(example["concepts"]),
        "mode": "case", "example_id": example["example_id"],
        "question": bilingual(example["scenario_ar"], example["scenario_en"])})
    return [{"path_id": "inheritance_beginner", "title_ar": "فهم نظام المواريث في الإسلام",
             "title_en": "Understanding Islamic Inheritance", "difficulty": "beginner",
             "steps": path_steps}]
