"""Question -> Qwen parser -> local sources -> Qwen reasoner -> verifier."""

import json

from backend.llm.qwen_reasoner import analyze_case
from backend.parsing.qwen_relation_parser import parse_relations
from backend.rag.retriever import retrieve_rules
from backend.rag.coverage import check_source_coverage
from backend.rules.case_features import build_case_features
from backend.verifier.fractions import verify_and_normalize
from backend.sources.router import enrich_sources
from backend.rag.fiqh.retriever import retrieve_fiqh
from backend.rules.case_readiness import assess_case
from backend.rules.population import prepare_case
from backend.rules.residuaries import include_children_rule
from backend.rules.safety import SolverReferral


def run_pipeline(question: str, *, parsed_relations: dict | None = None, deterministic: bool = True) -> dict:
    parsed = parsed_relations if parsed_relations is not None else (
        parse_relations(question) if question.strip() else {"mentioned_relatives": []})
    features = build_case_features(parsed)
    normalized = {"mentioned_relatives": [{"relation": r, "count": n} for r, n in features["relations"].items()]}
    sources = include_children_rule(normalized, retrieve_rules(normalized, features))
    enriched_sources = enrich_sources(sources)
    try:
        fiqh_evidence = retrieve_fiqh(question)
        fiqh_retrieval = {"status": "available" if fiqh_evidence else "empty"}
    except (RuntimeError, ValueError, OSError) as exc:
        fiqh_evidence = []
        fiqh_retrieval = {"status": "unavailable", "error": str(exc)}
    # Evidence never enters structured-rule coverage or grants new rulings.
    population = prepare_case(parsed)
    eligible = {"mentioned_relatives": [{"relation": r, "count": n} for r, n in population.eligible_to_inherit.items()]}
    coverage = check_source_coverage(eligible, sources)
    if population.excluded_by_another_heir:
        coverage["covered_relations"] += list(population.excluded_by_another_heir)
        coverage["coverage_ratio"] = len(coverage["covered_relations"]) / len(population.present_in_case)
    readiness = assess_case(question, parsed, sources)
    readiness["eligibility"] = {
        "present_in_case": population.present_in_case,
        "eligible_to_inherit": population.eligible_to_inherit,
        "excluded_by_another_heir": population.excluded_by_another_heir,
    }
    if readiness["decision_state"] == "ready" and not coverage["is_sufficient"]:
        readiness.update(decision_state="specialist_referral", reason="unsupported_heir_or_residuary")
    output = {
        "question": question,
        "parsed_relations": parsed,
        "case_features": features,
        "sources": enriched_sources,
        "fiqh_evidence": fiqh_evidence,
        "fiqh_retrieval": fiqh_retrieval,
        "source_coverage": coverage,
        "decision_state": readiness["decision_state"] if readiness["decision_state"] != "ready" else "specialist_referral",
        "clarification_question": readiness["clarification_question"],
        "case_readiness": readiness,
        "result": None,
    }
    if readiness["decision_state"] != "ready" or not coverage["is_sufficient"]:
        return output

    if deterministic:
        from backend.rules.distribution import allocate
        try:
            result = allocate(parsed, sources)
        except SolverReferral as exc:
            output["case_readiness"].update(decision_state="specialist_referral", reason=exc.reason)
            return output
        except (ValueError, KeyError, ZeroDivisionError):
            return output
        output.update(decision_state="ready", result=result)
        return output

    result = analyze_case(
        question=question,
        parsed_relations=parsed,
        case_features=features,
        sources=sources,
        fiqh_evidence=fiqh_evidence,
    )
    result = verify_and_normalize(result)
    output.update(decision_state="ready", result=result)
    return output


if __name__ == "__main__":
    print("\nMAWARITH AI - Qwen Pipeline")
    print("اكتب مسألة المواريث ثم اضغط Enter.\n")

    question = input("المسألة: ").strip()

    if not question:
        raise SystemExit("لم يتم إدخال مسألة.")

    output = run_pipeline(question)

    print("\n===== RESULT =====\n")

    print(
        json.dumps(
            output,
            ensure_ascii=False,
            indent=2
        )
    )
