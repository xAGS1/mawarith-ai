"""Runtime corpus selection and validation of existing educational payloads."""
import hashlib
import os


def cloud_sources() -> bool:
    mode = os.getenv("SOURCE_MODE", "local").strip().lower()
    if mode not in {"local", "cloud"}:
        raise ValueError("SOURCE_MODE must be local or cloud")
    return mode == "cloud"


def payload_record(payload: dict, source_id: str | None = None) -> dict:
    source = {**{k: v for k, v in payload.items() if k not in {"text", "exact_text", "normalized_text", "source", "embedding_model"}},
              **(payload.get("source") or {})}
    text = payload.get("exact_text", payload.get("text"))
    if not isinstance(text, str) or not text.strip() or not source.get("source_name"):
        raise ValueError("Cloud source payload is incomplete")
    if source_id and source.get("source_id") != source_id:
        raise ValueError("Cloud source identity mismatch")
    if source.get("retrieval_eligible") is False or (source.get("verified_source") is not True and
            not (source.get("source_type") == "quran" and source.get("immutable_text") is True)):
        raise ValueError("Cloud source is not approved for retrieval")
    digest = source.get("excerpt_sha256")
    if digest and hashlib.sha256(text.encode()).hexdigest() != digest:
        raise ValueError("Cloud source excerpt checksum mismatch")
    return {"text": text, "source": source}


def cloud_candidates(query: str, collection: str, top_k: int, *, source_id=None, source_type=None):
    from backend.rag.fiqh.embeddings import embed_texts, embedding_model_name
    from backend.rag.fiqh.vector_store import QdrantFiqhStore
    store = QdrantFiqhStore(collection=collection)
    filters = [{"key": "embedding_model", "match": {"value": embedding_model_name()}}]
    if source_id:
        filters.append({"key": "source_id", "match": {"value": source_id}})
    if source_type:
        filters.append({"key": "source_type", "match": {"value": source_type}})
    hits = store._request("POST", f"/collections/{collection}/points/query", {
        "query": embed_texts([query])[0], "limit": top_k, "filter": {"must": filters},
        "with_payload": True, "with_vector": False})["points"]
    records = []
    for hit in hits:
        if hit["payload"].get("embedding_model") != embedding_model_name():
            raise ValueError("Cloud source embedding model mismatch")
        record = payload_record(hit["payload"], source_id)
        if source_type and record["source"].get("source_type") != source_type:
            raise ValueError("Cloud source type mismatch")
        records.append({**record, "score": hit["score"]})
    return records
