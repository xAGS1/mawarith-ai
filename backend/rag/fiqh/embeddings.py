"""Lazy local BGE-M3 dense embeddings, independent of the reasoning LLM."""

from functools import lru_cache
import math
import os


DIMENSION = 1024


class FiqhEmbeddingError(RuntimeError):
    pass


def embedding_model_name() -> str:
    return os.getenv("FIQH_EMBEDDING_MODEL", "BAAI/bge-m3")


def validate_vectors(vectors: list, expected_count: int) -> list[list[float]]:
    if len(vectors) != expected_count:
        raise FiqhEmbeddingError("Embedding count does not match source count")
    normalized = []
    for vector in vectors:
        if len(vector) != DIMENSION:
            raise FiqhEmbeddingError(f"Expected {DIMENSION}-dimensional BGE-M3 vectors")
        values = [float(v) for v in vector]
        if not all(math.isfinite(v) for v in values) or not any(values):
            raise FiqhEmbeddingError("Embedding vectors must be finite and nonzero")
        normalized.append(values)
    return normalized


@lru_cache(maxsize=1)
def _load_model(name: str):
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(name, trust_remote_code=False)
    except Exception as exc:
        raise FiqhEmbeddingError("Cannot load local BGE-M3; install requirements-fiqh.txt and prepare the model") from exc
    if model.get_sentence_embedding_dimension() != DIMENSION:
        raise FiqhEmbeddingError("Configured embedding model is not compatible with BGE-M3's 1024 dimensions")
    return model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise FiqhEmbeddingError("Embedding input must be nonempty exact source text")
    model = _load_model(embedding_model_name())
    try:
        vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True).tolist()
    except Exception as exc:
        raise FiqhEmbeddingError("Local BGE-M3 encoding failed") from exc
    return validate_vectors(vectors, len(texts))
