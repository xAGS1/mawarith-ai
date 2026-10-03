"""Retrieve exact approved fiqh excerpts as supporting evidence only."""

import json

from backend.rag.fiqh.embeddings import embed_texts, embedding_model_name
from backend.rag.fiqh.schemas import FiqhChunk
from backend.rag.fiqh.vector_store import FiqhStoreError, QdrantFiqhStore, build_filter, load_chunks


def retrieve_fiqh(query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Fiqh query must be nonempty")
    if type(top_k) is not int or not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    build_filter(filters)  # Validate even when the corpus is empty.
    chunks = load_chunks()
    if not chunks:
        return []
    approved = {chunk["chunk_id"]: chunk for chunk in chunks}
    store = QdrantFiqhStore()
    store.ensure_collection()
    hits = store.query(embed_texts([query])[0], top_k, filters)
    evidence = []
    for hit in hits:
        payload = dict(hit["payload"])
        model_name = payload.pop("embedding_model", None)
        try:
            chunk = FiqhChunk.model_validate(payload).model_dump(mode="json")
        except ValueError as exc:
            raise FiqhStoreError("Retrieved payload has invalid approved-source provenance") from exc
        if model_name != embedding_model_name() or approved.get(chunk["chunk_id"]) != chunk:
            raise FiqhStoreError("Retrieved payload does not match the locally approved source corpus/model")
        evidence.append({"score": float(hit["score"]), "text": chunk["text"],
                         "source": {k: v for k, v in chunk.items() if k != "text"}})
    return evidence


def main():
    query = input("اكتب سؤال البحث الفقهي: ").strip()
    try:
        results = retrieve_fiqh(query)
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not results:
        print("لا توجد مقتطفات معتمدة مطابقة؛ قد يكون المتن المحلي فارغا.")


if __name__ == "__main__":
    main()
