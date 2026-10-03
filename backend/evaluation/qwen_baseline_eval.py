import argparse
import json
from pathlib import Path

from backend.pipeline.qwen_pipeline import run_pipeline


def normalize_heir_list(items):
    normalized = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        normalized.append((str(item.get("heir", "")).strip(), int(item.get("count", 0))))
    return sorted(normalized)


def normalize_shares(items):
    normalized = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        normalized.append(
            (
                str(item.get("heir", "")).strip(),
                int(item.get("count", 0)),
                str(item.get("fraction", "")).strip(),
            )
        )
    return sorted(normalized)


def score_case(gold, pred):
    checks = {
        "heirs": normalize_heir_list(gold.get("heirs")) == normalize_heir_list(pred.get("heirs")),
        "blocked": normalize_heir_list(gold.get("blocked")) == normalize_heir_list(pred.get("blocked")),
        "shares": normalize_shares(gold.get("shares")) == normalize_shares(pred.get("shares")),
        "awl_or_radd": str(gold.get("awl_or_radd", "")).strip() == str(pred.get("awl_or_radd", "")).strip(),
        "post_tasil": gold.get("post_tasil", {}) == pred.get("post_tasil", {}),
    }
    checks["all_correct"] = all(checks.values())
    return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="Path to a QIAS JSON file containing question + output")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--out", default="baseline_results.json")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    counts = {
        "heirs": 0,
        "blocked": 0,
        "shares": 0,
        "awl_or_radd": 0,
        "post_tasil": 0,
        "all_correct": 0,
    }

    selected = data[: args.limit]

    for i, item in enumerate(selected, start=1):
        question = item["question"]
        gold = item["output"]

        print(f"[{i}/{len(selected)}] {item.get('id', '')}")

        try:
            pipeline_output = run_pipeline(question)
            pred = pipeline_output["result"]
            checks = score_case(gold, pred) if pred is not None else {key: False for key in counts}

            for key, value in checks.items():
                if value:
                    counts[key] += 1

            results.append({
                "id": item.get("id"),
                "question": question,
                "gold": gold,
                "prediction": pred,
                "parsed_relations": pipeline_output["parsed_relations"],
                "case_features": pipeline_output["case_features"],
                "sources": pipeline_output["sources"],
                "fiqh_evidence": pipeline_output["fiqh_evidence"],
                "fiqh_retrieval": pipeline_output["fiqh_retrieval"],
                "source_coverage": pipeline_output["source_coverage"],
                "decision_state": pipeline_output["decision_state"],
                "checks": checks,
            })
        except Exception as exc:
            results.append({
                "id": item.get("id"),
                "question": question,
                "error": str(exc),
            })

    summary = {
        "total": len(selected),
        "correct_counts": counts,
        "accuracy": {
            key: round(value / len(selected), 4) if selected else 0.0
            for key, value in counts.items()
        },
    }

    output = {"summary": summary, "results": results}

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"Saved: {out_path.resolve()}")


if __name__ == "__main__":
    main()
