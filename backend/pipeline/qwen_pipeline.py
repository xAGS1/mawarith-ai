"""Question -> Qwen parser -> local sources -> Qwen reasoner -> verifier."""

import json

from backend.llm.qwen_reasoner import analyze_case
from backend.parsing.qwen_relation_parser import parse_relations
from backend.rag.retriever import retrieve_rules
from backend.rag.coverage import check_source_coverage
from backend.rules.case_features import build_case_features
from backend.verifier.fractions import verify_and_normalize


def run_pipeline(question: str) -> dict:
    parsed = parse_relations(question)
    features = build_case_features(parsed)
    sources = retrieve_rules(parsed, features)
    coverage = check_source_coverage(parsed, sources)
    output = {
        "question": question,
        "parsed_relations": parsed,
        "case_features": features,
        "sources": sources,
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
    )
    result = verify_and_normalize(result)
    output.update(decision_state="ready", result=result)
    return output


if __name__ == "__main__":
    question = (
    "مات وترك زوجة وأخا شقيقا. "
    "ما هو نصيب كل وريث؟"
)
    print(json.dumps(run_pipeline(question), ensure_ascii=False, indent=2))
