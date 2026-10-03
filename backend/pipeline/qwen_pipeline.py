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


def run_pipeline(question: str) -> dict:
    parsed = parse_relations(question)
    features = build_case_features(parsed)
    sources = retrieve_rules(parsed, features)
    enriched_sources = enrich_sources(sources)
    try:
        fiqh_evidence = retrieve_fiqh(question)
        fiqh_retrieval = {"status": "available" if fiqh_evidence else "empty"}
    except (RuntimeError, ValueError, OSError) as exc:
        fiqh_evidence = []
        fiqh_retrieval = {"status": "unavailable", "error": str(exc)}
    # Evidence never enters structured-rule coverage or grants new rulings.
    coverage = check_source_coverage(parsed, sources)
    output = {
        "question": question,
        "parsed_relations": parsed,
        "case_features": features,
        "sources": enriched_sources,
        "fiqh_evidence": fiqh_evidence,
        "fiqh_retrieval": fiqh_retrieval,
        "source_coverage": coverage,
        "decision_state": "insufficient_sources",
        "result": None,
    }
    if not coverage["is_sufficient"]:
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
