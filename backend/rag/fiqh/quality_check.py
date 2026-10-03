"""Print and save the three requested real retrieval checks with exact context."""

import json

from backend.rag.fiqh.loader import DATA_DIR
from backend.rag.fiqh.retriever import retrieve_fiqh


QUERIES = [
    "ما حكم الأخت الشقيقة مع وجود البنات؟",
    "الأخت الشقيقة مع البنت عصبة مع الغير",
    "ميراث الأخت لأب مع البنات",
]


def main():
    report = []
    markdown = ["# Real fiqh retrieval checks", "", "Exact local source excerpts; supporting evidence only.", ""]
    for query in QUERIES:
        print(f"Query: {query}", flush=True)
        results = retrieve_fiqh(query, top_k=5)
        print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)
        report.append({"query": query, "results": results})
        markdown.extend([f"## {query}", ""])
        for rank, result in enumerate(results, 1):
            source = result["source"]
            markdown.extend([f"### Result {rank}", "",
                f"Score: {result['score']:.6f}; section: {source['section']!r}; offsets: {source['char_start']}–{source['char_end']}", ""])
            for label, part in [("Main hit", result), ("Previous chunk", result["previous_chunk"]), ("Next chunk", result["next_chunk"])]:
                markdown.extend([f"**{label}**", ""])
                if part is None:
                    markdown.extend(["Unavailable (document boundary).", ""])
                else:
                    metadata = part["source"]
                    markdown.extend([f"Section: {metadata['section']!r}; offsets: {metadata['char_start']}–{metadata['char_end']}", "",
                                     "```text", part["text"], "```", ""])
    output = DATA_DIR / "processed"
    output.mkdir(parents=True, exist_ok=True)
    (output / "retrieval_quality_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "retrieval_quality_report.md").write_text("\n".join(markdown), encoding="utf-8")
    print(f"Reports saved in {output}", flush=True)


if __name__ == "__main__":
    main()
