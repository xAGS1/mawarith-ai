"""Read-only retrieval diagnostics; never generates answers or writes Qdrant."""
import argparse
from datetime import datetime, timezone
from difflib import SequenceMatcher
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def diagnostics(hits):
    from backend.rules.educational_concepts import matching_text
    flags, duplicates = [], []
    for i, hit in enumerate(hits):
        text = matching_text(hit["text"])
        # Review candidates, not assertions that a religious rule is incomplete.
        if text.rstrip().endswith(":") or re.match(r"^(?:فان|فإن|وهو|وهي|عند|ثانيهما|اولهما|أولهما)\s", text.strip()):
            flags.append({"rank": i + 1, "reason": "possible missing antecedent or continuation"})
        for j in range(i):
            other = matching_text(hits[j]["text"])
            if text == other or SequenceMatcher(None, text, other, autojunk=False).ratio() >= .9:
                duplicates.append([j + 1, i + 1])
    return flags, duplicates


def recall(records):
    gold = [r for r in records if r.get("expected_source_ids")]
    return {f"Recall@{k}": (sum(len(set(r["expected_source_ids"]) &
        {h["source_id"] for h in r["results"][:k]}) / len(set(r["expected_source_ids"]))
        for r in gold) / len(gold) if gold else None) for k in (1, 3, 5)}


def run(questions, retrieve, top_k):
    from backend.rules.educational_concepts import matching_text
    records = []
    for question in questions:
        record = {**question, "results": [], "error": None}
        try:
            hits = retrieve(question["question"], top_k=top_k)
            flags, duplicates = diagnostics(hits)
            for rank, h in enumerate(hits, 1):
                s = h["source"]
                record["results"].append({"rank": rank, "source_id": s["chunk_id"],
                    "similarity_score": h["score"], "source_title": s.get("source_name"),
                    "section": s.get("section"), "topic": s.get("topic"),
                    "text_preview": h["text"][:600], "provenance": s,
                    "previous_chunk_id": (h.get("previous_chunk") or {}).get("source", {}).get("chunk_id"),
                    "next_chunk_id": (h.get("next_chunk") or {}).get("source", {}).get("chunk_id")})
            record.update(suspicious_chunks=flags, duplicate_ranks=duplicates)
            gold = set(question.get("expected_source_ids", []))
            if gold:
                record["no_relevant_retrieval"] = not gold.intersection(h["source_id"] for h in record["results"])
                record["relevance_basis"] = "pinned gold chunk IDs (ranked hits only; neighbors excluded)"
            else:
                anchors = question.get("topic_anchors", [])
                record["no_relevant_retrieval"] = not any(matching_text(a) in matching_text(h["text"])
                    for a in anchors for h in hits)
                record["relevance_basis"] = "lexical topic heuristic; requires manual review, excluded from recall"
        except (RuntimeError, ValueError, OSError) as exc:
            record["error"] = str(exc)
        records.append(record)
        print(f'{question["id"]}: {len(record["results"])} hits; error={record["error"] or "none"}', flush=True)
    return {"records": records, "metrics": recall(records),
        "gold_question_count": sum(bool(r.get("expected_source_ids")) for r in records),
        "weak_questions": [r["id"] for r in records if r.get("no_relevant_retrieval")],
        "failed_questions": [r["id"] for r in records if r["error"]]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=5, choices=range(5, 101))
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    questions = json.loads((here / "questions.json").read_text(encoding="utf-8"))
    from backend.rag.fiqh.vector_store import QdrantFiqhStore
    from backend.rag.fiqh.retriever import retrieve_fiqh
    from backend.rag.fiqh.embeddings import embedding_model_name
    store = QdrantFiqhStore()
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "host": store.host,
        "collection": store.collection, "embedding_model": embedding_model_name(), "top_k": args.top_k,
        "retrieval_only": True}
    try:
        store.ensure_collection(create=False)
    except (RuntimeError, ValueError, OSError) as exc:
        report.update(status="unavailable", error=str(exc), metrics=None, records=[])
    else:
        report.update(run(questions, retrieve_fiqh, args.top_k))
        report["status"] = "partial_failure" if report["failed_questions"] else "completed"
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    folder = here / "results"
    folder.mkdir(exist_ok=True)
    target = folder / ("retrieval_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ") + ".json")
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report.get(k) for k in ("status", "metrics", "weak_questions", "failed_questions", "error")}, ensure_ascii=False))
    print(f"Results: {target}")
    if report["status"] != "completed":
        print("Retry after restoring the existing Qdrant service/collection: python evaluation/rag_benchmark/run_retrieval_benchmark.py")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
