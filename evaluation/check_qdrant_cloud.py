"""Manual, read-only dense retrieval smoke check for both migrated collections."""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter

import requests

from backend.rag.fiqh.embeddings import embed_texts
from backend.rag.qdrant_auth import qdrant_auth_kwargs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", default="ما معنى العصبة؟")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--env-file", type=Path, help="Optionally load local .env; existing environment wins")
    args = parser.parse_args()
    if args.top_k < 1 or not args.question.strip():
        parser.error("Use a nonempty question and positive top-k")
    if args.env_file:
        from dotenv import load_dotenv

        if not args.env_file.is_file():
            parser.error("Environment file not found")
        load_dotenv(args.env_file, override=False)
    host = os.getenv("QDRANT_HOST")
    if not host or not os.getenv("QDRANT_API_KEY"):
        parser.error("Set QDRANT_HOST and QDRANT_API_KEY in the environment")

    started = perf_counter()
    try:
        vector = embed_texts([args.question])[0]
    except Exception as exc:
        print(f"Embedding failed ({type(exc).__name__}); no Qdrant requests sent.")
        return 1
    print(f"Local embedding latency: {perf_counter() - started:.3f}s")
    failures = 0
    for collection in ("mawarith_fiqh", "mawarith_uqu"):
        started = perf_counter()
        try:
            response = requests.post(
                f"{host.rstrip('/')}/collections/{collection}/points/query",
                json={"query": vector, "limit": args.top_k,
                      "with_payload": True, "with_vector": False},
                timeout=30, **qdrant_auth_kwargs(),
            )
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                raise ValueError("Query did not succeed")
            points = data["result"]["points"]
            results = []
            for point in points:
                payload = point.get("payload") or {}
                source = payload.get("source") or {}
                results.append({
                    "id": point["id"], "score": point["score"],
                    "source_name": payload.get("source_name") or source.get("source_name"),
                    "source_id": payload.get("source_id") or source.get("source_id"),
                })
            print(json.dumps({"collection": collection, "query_latency_seconds": round(perf_counter() - started, 3),
                              "results": results}, ensure_ascii=False, indent=2))
        except Exception as exc:
            # Never print exception bodies, headers, host or credentials.
            failures += 1
            print(f"{collection}: query failed ({type(exc).__name__}); latency {perf_counter() - started:.3f}s")
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
