"""Question -> Qwen parser -> local sources -> Qwen reasoner -> verifier."""

import json

from backend.llm.qwen_reasoner import analyze_case
from backend.parsing.qwen_relation_parser import parse_relations
from backend.rag.retriever import retrieve_rules


def run_pipeline(question: str) -> dict:
    parsed = parse_relations(question)
    sources = retrieve_rules(parsed)
    # analyze_case runs the Python fraction verifier after Qwen's output.
    result = analyze_case(
        question=question,
        parsed_relations=parsed,
        sources=sources,
    )
    return {
        "question": question,
        "parsed_relations": parsed,
        "sources": sources,
        "result": result,
    }


if __name__ == "__main__":
    question = "مات وترك زوجة وأما وابنين وبنت. ما هو نصيب كل وريث؟"
    print(json.dumps(run_pipeline(question), ensure_ascii=False, indent=2))
