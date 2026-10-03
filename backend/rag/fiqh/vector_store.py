"""Real Qdrant REST collection and indexing; no production fallback store."""

import argparse
import json
import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import requests

from backend.rag.fiqh.embeddings import DIMENSION, embed_texts, embedding_model_name, validate_vectors
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
            response = requests.request(method, self.host + path, json=body, timeout=10)
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
        vectors = validate_vectors(vectors, len(chunks))
        points = [{"id": str(uuid5(NAMESPACE_URL, chunk["chunk_id"])), "vector": vector,
                   "payload": build_payload(chunk)} for chunk, vector in zip(chunks, vectors)]
        if points:
            self._request("PUT", f"/collections/{self.collection}/points?wait=true", {"points": points})

    def query(self, vector: list[float], top_k: int = 5, filters: dict | None = None) -> list:
        validate_vectors([vector], 1)
        result = self._request("POST", f"/collections/{self.collection}/points/query",
                               {"query": vector, "limit": top_k, "filter": build_filter(filters),
                                "with_payload": True, "with_vector": False})
        return result["points"]


def index_chunks(path: Path | None = None, batch_size: int = 16) -> int:
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("Indexing batch size must be a positive integer")
    chunks = load_chunks(path)
    if not chunks:
        return 0  # Empty approved corpus is explicit; no fake store or vectors.
    store = QdrantFiqhStore()
    store.ensure_collection(create=True)  # Check Qdrant before loading a large model.
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        store.upsert(batch, embed_texts([chunk["text"] for chunk in batch]))
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chunks", type=Path, default=DATA_DIR / "processed" / "chunks.json")
    parser.add_argument("--check-connection", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_connection:
            print("Qdrant connected; collections:", QdrantFiqhStore().connect())
        else:
            count = index_chunks(args.chunks)
            print(f"Indexed {count} approved chunks" if count else "Empty approved corpus: no chunks indexed; Qdrant was not contacted")
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
