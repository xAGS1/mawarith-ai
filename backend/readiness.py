"""Dependency readiness checks; no generation or data mutations."""
import os
from urllib.parse import urlparse

from backend.llm.transport import selected_provider
from backend.rag.fiqh.embeddings import embed_texts, validate_vectors
from backend.rag.fiqh.vector_store import QdrantFiqhStore
from backend.rag.source_mode import cloud_sources


def _http_url(value):
    url = urlparse(value)
    return url.scheme in {"http", "https"} and bool(url.hostname)


def check_readiness():
    checks = {}
    try:
        provider = selected_provider()
        if provider == "fanar":
            checks["llm_configuration"] = bool(os.getenv("FANAR_API_KEY", "").strip()) and bool(
                os.getenv("FANAR_MODEL", "Fanar-C-2-27B").strip()) and _http_url(
                os.getenv("FANAR_BASE_URL", "https://api.fanar.qa/v1"))
        else:
            import requests
            response = requests.get(os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/") + "/api/tags", timeout=10)
            response.raise_for_status()
            names = {m.get("name") for m in response.json()["models"]}
            checks["llm_configuration"] = os.getenv("OLLAMA_MODEL", "qwen3:8b") in names
    except Exception:
        checks["llm_configuration"] = False
    try:
        cloud = cloud_sources()
        checks["source_configuration"] = not cloud or (
            _http_url(os.getenv("QDRANT_HOST", "")) and bool(os.getenv("QDRANT_API_KEY", "").strip()))
    except Exception:
        checks["source_configuration"] = False
    try:
        store = QdrantFiqhStore()
        names = store.connect()
        checks["qdrant_reachable"] = True
        for collection, expected in (("mawarith_fiqh", 1767), ("mawarith_uqu", 47)):
            try:
                if collection not in names:
                    checks[collection] = False
                    continue
                collection_store = QdrantFiqhStore(collection=collection)
                collection_store.ensure_collection(create=False)
                checks[collection] = collection_store.points_count() == expected
            except Exception:
                checks[collection] = False
    except Exception:
        checks.update(qdrant_reachable=False, mawarith_fiqh=False, mawarith_uqu=False)
    try:
        validate_vectors(embed_texts(["readiness probe"], batch_size=1), 1)
        checks["embedding_usable"] = True
    except Exception:
        checks["embedding_usable"] = False
    ready = all(checks.values())
    # Never serialize exception messages, environment values or HTTP bodies.
    return ready, {"status": "ready" if ready else "not_ready", "checks": checks}
