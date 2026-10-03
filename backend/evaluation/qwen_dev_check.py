import json
from pathlib import Path
import requests

from backend.pipeline.qwen_pipeline import run_pipeline


DATASET = "data/qias/qias2025_almawarith_part2.json"
LIMIT = 5


def main():
    path = Path(DATASET)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    selected = data[:LIMIT]

    results = []

    for i, item in enumerate(selected, start=1):
        question = item["question"]

        print(f"\n===== CASE {i}/{LIMIT} =====")
        print("ID:", item.get("id"))
        print("QUESTION:")
        print(question)

        try:
            pipeline_output = run_pipeline(question)
            prediction = pipeline_output["result"]

            result = {
                "id": item.get("id"),
                "question": question,
                "prediction": prediction,
                "parsed_relations": pipeline_output["parsed_relations"],
                "sources": pipeline_output["sources"],
                "gold": item["output"],
                "status": "completed",
            }

            print("\nQWEN OUTPUT:")
            print(
                json.dumps(
                    prediction,
                    ensure_ascii=False,
                    indent=2,
                )
            )

        except requests.exceptions.Timeout:
            print("\nTIMEOUT")

            result = {
                "id": item.get("id"),
                "question": question,
                "prediction": None,
                "gold": item["output"],
                "status": "timeout",
            }

        except Exception as exc:
            print(f"\nERROR: {exc}")

            result = {
                "id": item.get("id"),
                "question": question,
                "prediction": None,
                "gold": item["output"],
                "status": "error",
                "error": str(exc),
            }

        results.append(result)

        # Save after every case
        with open(
            "dev_check_results.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                results,
                f,
                ensure_ascii=False,
                indent=2,
            )

    print("\nFinished.")
    print("Results saved to dev_check_results.json")


if __name__ == "__main__":
    main()
