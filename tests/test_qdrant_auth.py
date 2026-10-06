from unittest.mock import Mock

import pytest

from backend.rag.fiqh.vector_store import QdrantFiqhStore
from backend.rag import rebuild_uqu
from backend.rag.qdrant_auth import qdrant_auth_kwargs


@pytest.mark.parametrize("key", [None, "", "synthetic-test-key"])
def test_store_optional_auth_and_existing_collection_configuration(monkeypatch, key):
    monkeypatch.delenv("QDRANT_API_KEY", raising=False)
    monkeypatch.delenv("QDRANT_HOST", raising=False)
    monkeypatch.delenv("FIQH_COLLECTION", raising=False)
    assert QdrantFiqhStore().host == "http://localhost:6333"
    assert QdrantFiqhStore().collection == "mawarith_fiqh"
    if key is not None:
        monkeypatch.setenv("QDRANT_API_KEY", key)
    monkeypatch.setenv("QDRANT_HOST", "https://example.invalid:6333/")
    monkeypatch.setenv("FIQH_COLLECTION", "existing_custom_collection")
    request = Mock(return_value=Mock(json=lambda: {"status": "ok", "result": {"count": 7}}))
    monkeypatch.setattr("backend.rag.fiqh.vector_store.requests.request", request)
    store = QdrantFiqhStore()
    assert store.points_count() == 7
    expected = {"headers": {"api-key": key}} if key else {}
    request.assert_called_once_with(
        "POST", "https://example.invalid:6333/collections/existing_custom_collection/points/count",
        json={"exact": True}, timeout=10, **expected,
    )
    assert qdrant_auth_kwargs() == expected
    assert QdrantFiqhStore(host="http://override:6333", collection="override").collection == "override"


@pytest.mark.parametrize("key", [None, "synthetic-test-key"])
def test_uqu_indexing_auth_preserves_isolated_collection(monkeypatch, key):
    monkeypatch.delenv("QDRANT_API_KEY", raising=False)
    if key:
        monkeypatch.setenv("QDRANT_API_KEY", key)
    monkeypatch.setenv("QDRANT_HOST", "https://example.invalid:6333/")
    monkeypatch.setattr(rebuild_uqu, "embed_texts", lambda _: [[1.] * 1024])
    calls = []
    stored = []

    def request(method, url, **kwargs):
        calls.append((url, kwargs))
        result = {}
        if url.endswith("/collections"):
            result = {"collections": []}
        elif method == "PUT" and "/points?" in url:
            stored.extend(kwargs["json"]["points"])
        elif url.endswith("/points"):
            result = [{"id": p["id"]} for p in stored]
        elif url.endswith("/points/count"):
            result = {"count": len(stored)}
        return Mock(json=lambda: {"status": "ok", "result": result})

    monkeypatch.setattr(rebuild_uqu.requests, "request", request)
    source = {"source_id": "uqu_mawarith_1", "verified_source": True,
              "chunk_id": "test", "char_start": 0, "excerpt_sha256": "test-hash"}
    assert rebuild_uqu.index_uqu([{"text": "synthetic", "source": source}]) == 1
    assert all(url.startswith("https://example.invalid:6333/") for url, _ in calls)
    assert all("mawarith_fiqh" not in url for url, _ in calls)
    assert any("/collections/mawarith_uqu" in url for url, _ in calls)
    for _, kwargs in calls:
        if key:
            assert kwargs["headers"] == {"api-key": key}
        else:
            assert "headers" not in kwargs
