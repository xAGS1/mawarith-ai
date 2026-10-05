"""Explicit live check of the existing production RAG with optional page context."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.pipeline.educational_pipeline import run_request


def main():
    records = []
    context = {"slug": "awl", "title": "العول"}
    for question in ("ليش أصل المسألة يزيد؟", "طيب وش الفرق بينه وبين الرد؟"):
        trace = {}
        response = run_request(question, "learn", concept_context=context, debug_trace=trace)
        records.append({"question": question, "concept_context": context,
                        "response": response, "trace": trace})
        print(json.dumps({"question": question, "evidence_status": response.get("evidence_status"),
                          "answer": response["answer"], "sources": response.get("sources"),
                          "retrieval_query": trace.get("retrieval_query")}, ensure_ascii=False), flush=True)
    # Source-bearing diagnostics stay in the ignored processed directory.
    output = Path("data/fiqh/dorar_inheritance/processed/concept_tutor_live.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf8")


if __name__ == "__main__":
    main()
