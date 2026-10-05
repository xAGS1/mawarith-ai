"""Retrieve exact approved fiqh excerpts as supporting evidence only."""

import json

from backend.rag.fiqh.embeddings import embed_texts, embedding_model_name
from backend.rag.fiqh.schemas import FiqhChunk
from backend.rag.fiqh.query_expansion import expand_embedding_query, concept_query_filters
from backend.rag.fiqh.vector_store import FiqhStoreError, QdrantFiqhStore, build_filter, load_chunks


def retrieve_fiqh(query: str, top_k: int = 5, filters: dict | None = None, *, semantic_only: bool = False) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Fiqh query must be nonempty")
    if type(top_k) is not int or not 1 <= top_k <= 100:
        raise ValueError("top_k must be between 1 and 100")
    build_filter(filters)  # Validate even when the corpus is empty.
    chunks = load_chunks()
    if not chunks:
        return []
    approved = {chunk["chunk_id"]: chunk for chunk in chunks}
    documents = {}
    for chunk in chunks:
        documents.setdefault((chunk["input_file"], chunk["document_sha256"]), []).append(chunk)
    neighbors = {}
    for document in documents.values():
        document.sort(key=lambda c: (c["char_start"], c["char_end"], c["chunk_id"]))
        for index, chunk in enumerate(document):
            neighbors[chunk["chunk_id"]] = (document[index - 1] if index else None,
                                           document[index + 1] if index + 1 < len(document) else None)
    store = QdrantFiqhStore()
    store.ensure_collection()
    embedding_query = query if semantic_only else expand_embedding_query(query)
    query_filters = filters if semantic_only else concept_query_filters(query, filters)
    hits = store.query(embed_texts([embedding_query])[0], top_k, query_filters)
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
        def excerpt(part):
            return {"text": part["text"], "source": {k: v for k, v in part.items() if k != "text"}} if part else None
        previous, following = neighbors[chunk["chunk_id"]]
        evidence.append({"score": float(hit["score"]), **excerpt(chunk),
                         "previous_chunk": excerpt(previous), "next_chunk": excerpt(following)})
    return evidence


def main():
    query = input("السؤال: ").strip()
    try:
        results = retrieve_fiqh(query)
    except (RuntimeError, ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if not results:
        print("لا توجد مقتطفات معتمدة مطابقة؛ قد يكون المتن المحلي فارغا.")


if __name__ == "__main__":
    main()
