"""Real Qdrant REST collection and indexing; no production fallback store."""

import argparse
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import requests

from backend.rag.qdrant_auth import qdrant_auth_kwargs

from backend.rag.fiqh.embeddings import DIMENSION, embed_texts, embedding_model_name, validate_vectors, embedding_batch_size
from backend.rag.fiqh.loader import DATA_DIR
from backend.rag.fiqh.schemas import FiqhChunk, PUBLISHER, SOURCE_NAME


class FiqhStoreError(RuntimeError):
    pass


def load_chunks(path: Path | None = None) -> list[dict]:
    path = path or DATA_DIR / "processed" / "chunks.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Processed fiqh corpus must be a list of approved chunks")
    return [FiqhChunk.model_validate(chunk).model_dump(mode="json") for chunk in data]


def build_payload(chunk: dict, model_name: str | None = None) -> dict:
    payload = FiqhChunk.model_validate(chunk).model_dump(mode="json")
    return {**payload, "embedding_model": model_name or embedding_model_name()}


def point_id(chunk_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, chunk_id))


def build_filter(filters: dict | None = None) -> dict:
    must = [
        {"key": "verified_source", "match": {"value": True}},
        {"key": "source_type", "match": {"value": "fiqh"}},
        {"key": "source_name", "match": {"value": SOURCE_NAME}},
        {"key": "publisher", "match": {"value": PUBLISHER}},
        {"key": "embedding_model", "match": {"value": embedding_model_name()}},
    ]
    for key, value in (filters or {}).items():
        if key not in {"topic", "source_name", "section", "volume"}:
            raise ValueError(f"Unsupported fiqh filter: {key}")
        if value is None:
            must.append({"is_null": {"key": key}})
        elif (key == "volume" and type(value) is int and value > 0) or (key != "volume" and isinstance(value, str)):
            must.append({"key": key, "match": {"value": value}})
        else:
            raise ValueError(f"Invalid fiqh filter value: {key}")
    return {"must": must}


class QdrantFiqhStore:
    def __init__(self, host: str | None = None, collection: str | None = None):
        self.host = (host or os.getenv("QDRANT_HOST", "http://localhost:6333")).rstrip("/")
        self.collection = collection or os.getenv("FIQH_COLLECTION", "mawarith_fiqh")
        if not self.collection or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in self.collection):
            raise ValueError("Invalid Qdrant collection name")

    def _request(self, method: str, path: str, body: dict | None = None):
        try:
            response = requests.request(method, self.host + path, json=body, timeout=10,
                                        **qdrant_auth_kwargs())
            response.raise_for_status()
            data = response.json()
            if data.get("status") != "ok":
                raise ValueError("Qdrant did not report success")
            return data["result"]
        except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
            raise FiqhStoreError(f"Qdrant request failed at {self.host}{path}: {exc}") from exc

    def connect(self) -> list[str]:
        result = self._request("GET", "/collections")
        return [c["name"] for c in result["collections"]]

    def ensure_collection(self, create: bool = False):
        names = self.connect()
        path = f"/collections/{self.collection}"
        if self.collection not in names:
            if not create:
                raise FiqhStoreError(f"Qdrant collection {self.collection} is not indexed; run backend.rag.fiqh.vector_store")
            self._request("PUT", path, {"vectors": {"size": DIMENSION, "distance": "Cosine"}})
        info = self._request("GET", path)
        try:
            vectors = info["config"]["params"]["vectors"]
        except (KeyError, TypeError) as exc:
            raise FiqhStoreError("Qdrant returned an invalid collection configuration") from exc
        if not isinstance(vectors, dict):
            raise FiqhStoreError("Qdrant collection does not expose compatible dense vectors")
        if vectors.get("size") != DIMENSION or vectors.get("distance") != "Cosine":
            raise FiqhStoreError("Qdrant collection has incompatible vector dimensions or distance")

    def upsert(self, chunks: list[dict], vectors: list[list[float]]):
        if any(len(chunk["text"]) < 100 for chunk in chunks):
            raise FiqhStoreError("Standalone fiqh fragments below 100 characters cannot be indexed; merge with approved adjacent source text")
        vectors = validate_vectors(vectors, len(chunks))
        points = [{"id": point_id(chunk["chunk_id"]), "vector": vector,
                   "payload": build_payload(chunk)} for chunk, vector in zip(chunks, vectors)]
        if points:
            self._request("PUT", f"/collections/{self.collection}/points?wait=true", {"points": points})

    def query(self, vector: list[float], top_k: int = 5, filters: dict | None = None) -> list:
        validate_vectors([vector], 1)
        result = self._request("POST", f"/collections/{self.collection}/points/query",
                               {"query": vector, "limit": top_k, "filter": build_filter(filters),
                                "with_payload": True, "with_vector": False})
        return result["points"]

    def points_count(self) -> int:
        return self._request("POST", f"/collections/{self.collection}/points/count", {"exact": True})["count"]

    def prune_stale_points(self, chunks: list[dict]):
        current = {point_id(chunk["chunk_id"]) for chunk in chunks}
        files = sorted({chunk["input_file"] for chunk in chunks})
        query_filter = build_filter()
        query_filter["must"].append({"key": "input_file", "match": {"any": files}})
        offset = None
        stale = []
        while True:
            body = {"limit": 256, "filter": query_filter, "with_payload": False, "with_vector": False}
            if offset is not None:
                body["offset"] = offset
            result = self._request("POST", f"/collections/{self.collection}/points/scroll", body)
            stale.extend(point["id"] for point in result["points"] if str(point["id"]) not in current)
            offset = result.get("next_page_offset")
            if offset is None:
                break
        for start in range(0, len(stale), 256):
            self._request("POST", f"/collections/{self.collection}/points/delete?wait=true", {"points": stale[start:start + 256]})
        print(f"Removed {len(stale)} obsolete points for the current source files; collection retained", flush=True)


def index_chunks(path: Path | None = None, batch_size: int | None = None, prune_stale: bool = False) -> int:
    batch_size = embedding_batch_size(batch_size)
    chunks = load_chunks(path)
    unique = {}
    for chunk in chunks:
        if chunk["chunk_id"] in unique and unique[chunk["chunk_id"]] != chunk:
            raise FiqhStoreError("Conflicting source chunks share the same chunk_id")
        unique[chunk["chunk_id"]] = chunk
    chunks = list(unique.values())
    if any(len(chunk["text"]) < 100 for chunk in chunks):
        raise FiqhStoreError("Processed corpus contains standalone fragments below 100 characters; merge source segments before indexing")
    if not chunks:
        return 0  # Empty approved corpus is explicit; no fake store or vectors.
    store = QdrantFiqhStore()
    store.ensure_collection(create=True)  # Check Qdrant before loading a large model.
    print(f"Embedding batch size: {batch_size}; unique chunks: {len(chunks)}", flush=True)
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        print(f"Embedding batch {start // batch_size + 1}/{total_batches}", flush=True)
        store.upsert(batch, embed_texts([chunk["text"] for chunk in batch], batch_size=batch_size))
        print(f"Upserted {start + len(batch)}/{len(chunks)}", flush=True)
    if prune_stale:
        store.prune_stale_points(chunks)
    count = store.points_count()
    print(f"Qdrant points_count: {count}; expected unique chunks: {len(chunks)}", flush=True)
    if count != len(chunks):
        raise FiqhStoreError(f"Qdrant contains {count} points, expected {len(chunks)}. Existing unrelated/stale points were not deleted; inspect the collection.")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=DATA_DIR / "processed" / "chunks.json")
    parser.add_argument("--check-connection", action="store_true")
    parser.add_argument("--batch-size", type=int, help="Override FIQH_EMBEDDING_BATCH_SIZE (default 32)")
    parser.add_argument("--sync-processed", action="store_true", help="After successful upserts, remove obsolete points for the same source files")
    args = parser.parse_args()
    try:
        if args.check_connection:
            print("Qdrant connected; collections:", QdrantFiqhStore().connect())
        else:
            count = index_chunks(args.chunks, batch_size=args.batch_size, prune_stale=args.sync_processed)
            print(f"Indexed {count} approved chunks" if count else "Empty approved corpus: no chunks indexed; Qdrant was not contacted")
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
