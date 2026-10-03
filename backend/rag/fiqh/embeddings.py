"""Lazy local BGE-M3 dense embeddings, independent of the reasoning LLM."""

from functools import lru_cache
import math
import os


DIMENSION = 1024


class FiqhEmbeddingError(RuntimeError):
    pass


def embedding_model_name() -> str:
    return os.getenv("FIQH_EMBEDDING_MODEL", "BAAI/bge-m3")


def embedding_batch_size(value: int | None = None) -> int:
    if value is None:
        try:
            value = int(os.getenv("FIQH_EMBEDDING_BATCH_SIZE", "32"))
        except ValueError as exc:
            raise FiqhEmbeddingError("FIQH_EMBEDDING_BATCH_SIZE must be a positive integer") from exc
    if type(value) is not int or value < 1:
        raise FiqhEmbeddingError("Embedding batch size must be a positive integer")
    return value


def select_embedding_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception as exc:
        raise FiqhEmbeddingError("Cannot detect the Torch embedding device; CUDA detection failed") from exc


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
    device = select_embedding_device()
    print(f"Embedding device: {device}", flush=True)
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(name, device=device, trust_remote_code=False)
        if device == "cuda":
            model.half()  # Reduce VRAM use on an 8GB laptop GPU.
    except Exception as exc:
        raise FiqhEmbeddingError(f"Cannot initialize BGE-M3 on {device}; no CPU fallback was attempted: {exc}") from exc
    dimension_method = getattr(model, "get_embedding_dimension", None)
    dimension = dimension_method() if callable(dimension_method) else model.get_sentence_embedding_dimension()
    if dimension != DIMENSION:
        raise FiqhEmbeddingError("Configured embedding model is not compatible with BGE-M3's 1024 dimensions")
    return model


def embed_texts(texts: list[str], batch_size: int | None = None) -> list[list[float]]:
    if not texts:
        return []
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise FiqhEmbeddingError("Embedding input must be nonempty exact source text")
    model = _load_model(embedding_model_name())
    batch_size = embedding_batch_size(batch_size)
    try:
        vectors = model.encode(texts, batch_size=batch_size, normalize_embeddings=True,
                               convert_to_numpy=True, show_progress_bar=False).tolist()
    except Exception as exc:
        raise FiqhEmbeddingError(f"Local BGE-M3 encoding failed (batch size {batch_size}); no CPU fallback was attempted. Reduce FIQH_EMBEDDING_BATCH_SIZE for CUDA out-of-memory errors: {exc}") from exc
    return validate_vectors(vectors, len(texts))
