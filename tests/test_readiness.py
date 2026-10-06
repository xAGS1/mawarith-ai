from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from backend import readiness
from backend.app import app


@pytest.fixture
def configured(monkeypatch):
    for name, value in {"LLM_PROVIDER": "fanar", "FANAR_API_KEY": "synthetic-secret",
                        "SOURCE_MODE": "cloud", "QDRANT_HOST": "https://example.invalid",
                        "QDRANT_API_KEY": "synthetic-qdrant-secret"}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.delenv("FANAR_MODEL", raising=False)
    monkeypatch.delenv("FANAR_BASE_URL", raising=False)
    counts = {"mawarith_fiqh": 1767, "mawarith_uqu": 47}
    stores = {}
    def constructor(collection=None):
        name = collection or "mawarith_fiqh"
        if name not in stores:
            store = Mock()
            store.connect.return_value = list(counts)
            store.points_count.side_effect = lambda: counts[name]
            stores[name] = store
        return stores[name]
    monkeypatch.setattr(readiness, "QdrantFiqhStore", constructor)
    embed = Mock(return_value=[[1.] * 1024])
    monkeypatch.setattr(readiness, "embed_texts", embed)
    return counts, stores, embed


def test_ready_and_health_unchanged(configured):
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    response = client.get("/ready")
    assert response.status_code == 200
    assert all(response.json()["checks"].values())
    assert "synthetic-secret" not in response.text
    for store in configured[1].values():
        store.ensure_collection.assert_called_with(create=False)
        store.upsert.assert_not_called()


@pytest.mark.parametrize("missing", ["FANAR_API_KEY", "QDRANT_HOST", "QDRANT_API_KEY"])
def test_missing_configuration_503(configured, monkeypatch, missing):
    monkeypatch.delenv(missing)
    assert TestClient(app).get("/ready").status_code == 503


@pytest.mark.parametrize("collection", ["mawarith_fiqh", "mawarith_uqu"])
def test_wrong_count_503(configured, collection):
    configured[0][collection] -= 1
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"][collection] is False


def test_missing_collection_503(configured):
    readiness.QdrantFiqhStore().connect.return_value = ["mawarith_fiqh"]
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["mawarith_uqu"] is False


def test_unreachable_qdrant_safe_response(configured):
    readiness.QdrantFiqhStore().connect.side_effect = RuntimeError("synthetic-secret")
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["qdrant_reachable"] is False
    assert "synthetic-secret" not in response.text


@pytest.mark.parametrize("vectors", [[], [[1.] * 3], [[0.] * 1024]])
def test_embedding_validation_503(configured, vectors):
    configured[2].return_value = vectors
    assert TestClient(app).get("/ready").status_code == 503


def test_embedding_api_failure_safe(configured):
    configured[2].side_effect = RuntimeError("synthetic-secret")
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert "synthetic-secret" not in response.text


def test_local_source_mode_does_not_require_cloud_key(configured, monkeypatch):
    monkeypatch.setenv("SOURCE_MODE", "local")
    monkeypatch.delenv("QDRANT_API_KEY")
    assert TestClient(app).get("/ready").status_code == 200
