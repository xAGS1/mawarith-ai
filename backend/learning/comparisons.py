"""Deterministic comparisons of shared, source-traceable properties."""
import re
from backend.learning.concept_catalog import find_curated_concept_by_query, get_curated_concept
from backend.learning.knowledge import verified_definition, verified_properties, render_value
from backend.rules.educational_concepts import matching_text


def _resolve(term: str):
    if term in {"التعصيب", "residuary inheritance"}:
        return get_curated_concept("residuary_heirs")
    return find_curated_concept_by_query(term)


def compare_concepts(concepts: list[dict], language: str) -> dict | None:
    if len(concepts) != 2 or concepts[0]["id"] == concepts[1]["id"]:
        return None
    if any(not c.get("verified") or not verified_definition(c) for c in concepts):
        return None
    properties = [verified_properties(c) for c in concepts]
    shared = [key for key in properties[0] if key in properties[1]]
    if not shared:
        return None
    answer, sources, excerpts = [], [], []
    for concept, facts in zip(concepts, properties):
        statements = []
        for name in shared:
            fact = facts[name]
            value = render_value(fact, language)
            if not value:
                return None
            record = concept["source_records"][fact["source_id"]]
            identity = (concept["id"], fact["source_id"])
            existing = next((s for s in sources if (s["concept_id"], s["source_id"]) == identity), None)
            if existing is None:
                evidence_id = f"E{len(sources) + 1}"
                source = {k: v for k, v in record.items() if k != "exact_text"}
                source.update(concept_id=concept["id"], source_id=fact["source_id"],
                              evidence_id=evidence_id, property_links=[])
                sources.append(source)
                text = value if fact["status"] == "source_verbatim" and isinstance(fact["value"], str) else record["exact_text"]
                excerpts.append({"text": text, "concept_id": concept["id"], "evidence_id": evidence_id,
                                 "source_id": fact["source_id"], "source_name": record.get("source_name"),
                                 "section": record.get("section"), "reference": concept.get("reference"),
                                 "source_url": record.get("source_url"), "immutable_text": True,
                                 "content_kind": "source_verbatim", "provenance": source})
            else:
                source, evidence_id = existing, existing["evidence_id"]
                excerpt = next(e for e in excerpts if e["evidence_id"] == evidence_id)
                if fact["status"] == "source_verbatim" and value not in excerpt["text"]:
                    excerpt["text"] = record["exact_text"]
            source["property_links"].append({"property": name, "source_id": fact["source_id"],
                "status": fact["status"], "reviewer": fact.get("reviewer"), "reviewed_at": fact.get("reviewed_at")})
            label = (("نص المصدر" if language == "ar" else "Source text") if fact["status"] == "source_verbatim"
                     else ("ملخص تعليمي مُراجع" if language == "ar" else "Reviewed educational summary"))
            statements.append(label + ": " + value + f" [{evidence_id}]")
        answer.append(concept[f"title_{language}"] + "\n" + "\n".join(statements))
    return {"answer": "\n\n".join(answer), "sources": sources, "source_excerpts": excerpts}


def curated_comparison(question: str, language: str) -> dict | None:
    query = matching_text(question.casefold()).strip(" ؟?.!")
    match = re.fullmatch(r"ما الفرق بين (.+?) و\s*(.+)", query)
    if match is None:
        match = re.fullmatch(r"what is the difference between (.+?) and (.+)", query)
    if match is None:
        return None
    concepts = [_resolve(term.strip()) for term in match.groups()]
    if any(c is None for c in concepts):
        return None
    return compare_concepts(concepts, language)
