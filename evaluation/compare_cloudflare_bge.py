"""Read-only local/Workers AI BGE-M3 comparison; no corpus or production changes."""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import quote

import requests

from backend.rag.fiqh.embeddings import _load_model, embed_texts, embedding_model_name, validate_vectors
from backend.rag.qdrant_auth import qdrant_auth_kwargs

QUERIES = ("ما معنى العصبة؟", "ما معنى العول؟", "نصيب الزوجة مع وجود ابن")
COLLECTIONS = ("mawarith_fiqh", "mawarith_uqu")


def remote_embedding(question, account, token):
    response = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{quote(account, safe='')}/ai/run/@cf/baai/bge-m3",
        headers={"Authorization": f"Bearer {token}"}, json={"text": [question]}, timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("success") is not True:
        raise ValueError("Cloudflare request unsuccessful")
    return validate_vectors(body["result"]["data"], 1)[0]


def query(host, collection, vector):
    started = perf_counter()
    response = requests.post(
        f"{host.rstrip('/')}/collections/{collection}/points/query",
        json={"query": vector, "limit": 3, "with_payload": False, "with_vector": False},
        timeout=30, **qdrant_auth_kwargs(),
    )
    response.raise_for_status()
    body = response.json()
    if body.get("status") != "ok":
        raise ValueError("Qdrant request unsuccessful")
    return {"query_latency_seconds": round(perf_counter() - started, 4),
            "top_3": [{"id": p["id"], "score": p["score"]} for p in body["result"]["points"]]}


def overlap(local, remote):
    a = {str(p["id"]) for p in local["top_3"]}
    b = {str(p["id"]) for p in remote["top_3"]}
    return {"common_ids": sorted(a & b), "count": len(a & b),
            "overlap_at_3": len(a & b) / 3,
            "jaccard": len(a & b) / len(a | b) if a | b else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, help="Optional .env; existing environment wins")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        if not args.env_file.is_file():
            parser.error("Environment file not found")
        load_dotenv(args.env_file, override=False)
    required = ("QDRANT_HOST", "QDRANT_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        parser.error("Missing environment variables: " + ", ".join(missing))
    if embedding_model_name() != "BAAI/bge-m3":
        parser.error("Local embedding configuration must be BAAI/bge-m3 for this comparison")
    started = perf_counter()
    try:
        _load_model(embedding_model_name())
    except Exception as exc:
        print(f"Local initialization failed ({type(exc).__name__})")
        return 1
    print(json.dumps({"local_initialization_seconds": round(perf_counter() - started, 4)}))
    failures = 0
    for question in QUERIES:
        record = {"question": question, "embeddings": {}, "collections": {}}
        vectors = {}
        for provider in ("local", "cloudflare"):
            started = perf_counter()
            try:
                vector = embed_texts([question])[0] if provider == "local" else remote_embedding(
                    question, os.environ["CLOUDFLARE_ACCOUNT_ID"], os.environ["CLOUDFLARE_API_TOKEN"])
                vectors[provider] = vector
                record["embeddings"][provider] = {"dimension": len(vector),
                    "latency_seconds": round(perf_counter() - started, 4)}
            except Exception as exc:
                failures += 1
                # Do not print HTTP bodies, exception messages, URLs or credentials.
                record["embeddings"][provider] = {"error_type": type(exc).__name__,
                    "latency_seconds": round(perf_counter() - started, 4)}
        for collection in COLLECTIONS:
            results = {}
            for provider, vector in vectors.items():
                try:
                    results[provider] = query(os.environ["QDRANT_HOST"], collection, vector)
                except Exception as exc:
                    failures += 1
                    results[provider] = {"error_type": type(exc).__name__}
            if all("top_3" in results.get(p, {}) for p in ("local", "cloudflare")):
                results["overlap"] = overlap(results["local"], results["cloudflare"])
            record["collections"][collection] = results
        print(json.dumps(record, ensure_ascii=False, indent=2))
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
