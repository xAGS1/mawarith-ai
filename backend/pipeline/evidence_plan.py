"""Backend-owned claim/source associations. These never grant rule coverage."""


def build_evidence_plan(rules: list[dict] = (), excerpts: list[dict] = (), concepts: list[dict] = ()) -> list[dict]:
    plan = []
    for rule in rules:
        source = rule.get("source", {})
        if not rule.get("rule_id") or not rule.get("rule") or not source.get("reference"):
            continue
        plan.append({"claim_id": f"C{len(plan) + 1}", "concept_or_rule_id": rule["rule_id"],
                     "source_id": f"{source.get('source_type')}:{source['reference']}",
                     "statement": rule["rule"], "support": "structured",
                     "exact_excerpt": source.get("arabic_text") if source.get("immutable_text") is True else None,
                     "applies_to": rule.get("applies_to", [])})
    for excerpt in excerpts:
        if not excerpt.get("text"):
            continue
        plan.append({"claim_id": f"C{len(plan) + 1}",
                     "concept_or_rule_id": excerpt.get("concept_id"),
                     "source_id": excerpt.get("evidence_id") or excerpt.get("provenance", {}).get("chunk_id") or f"E{len(plan) + 1}",
                     "statement": None, "support": "retrieved", "exact_excerpt": excerpt["text"]})
    for concept in concepts:
        evidence = next((e for e in excerpts if e.get("evidence_id") == concept.get("evidence_id")), None)
        if evidence is not None and concept.get("explanation"):
            plan.append({"claim_id": f"C{len(plan) + 1}", "concept_or_rule_id": concept["concept_id"],
                         "source_id": concept["evidence_id"], "statement": concept["explanation"],
                         "support": "structured", "exact_excerpt": evidence["text"]})
    return plan


def record_trace(trace: dict | None, understanding, origin: str, plan: list[dict], parsed: dict | None = None):
    if trace is not None:
        trace.update(detected_intent=understanding.intent, understanding_origin=origin,
                     language=understanding.language, explanation_depth=understanding.depth,
                     parsed_entities=parsed or {}, ambiguity_candidates=understanding.ambiguity_candidates,
                     selected_rule_ids=[c["concept_or_rule_id"] for c in plan if c["support"] == "structured"],
                     selected_source_ids=list(dict.fromkeys(c["source_id"] for c in plan)),
                     explanation_claims=plan)
