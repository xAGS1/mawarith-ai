from unittest.mock import Mock

import pytest
import requests

from backend.rag.fiqh import embeddings


@pytest.mark.parametrize("provider", [None, "local"])
def test_local_default_unchanged(monkeypatch, provider):
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    if provider:
        monkeypatch.setenv("EMBEDDING_PROVIDER", provider)
    model = Mock()
    model.encode.return_value.tolist.return_value = [[1.] * 1024]
    loader = Mock(return_value=model)
    monkeypatch.setattr(embeddings, "_load_model", loader)
    assert embeddings.embed_texts(["synthetic"]) == [[1.] * 1024]
    loader.assert_called_once_with(embeddings.embedding_model_name())
    assert model.encode.call_args.kwargs["normalize_embeddings"] is True


@pytest.fixture
def cloud(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "cloudflare")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "synthetic-account")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "synthetic-secret")
    monkeypatch.delenv("CLOUDFLARE_EMBEDDING_MODEL", raising=False)
    loader = Mock(side_effect=AssertionError("Local model must not load"))
    monkeypatch.setattr(embeddings, "_load_model", loader)
    return loader


def test_cloudflare_parsing_batching_and_model_metadata(monkeypatch, cloud):
    response = Mock()
    response.json.return_value = {"success": True, "result": {"data": [[.25] * 1024]}}
    post = Mock(return_value=response)
    monkeypatch.setattr(requests, "post", post)
    assert embeddings.embed_texts(["one", "two"], batch_size=1) == [[.25] * 1024] * 2
    assert post.call_count == 2
    assert post.call_args.args[0].endswith("/ai/run/@cf/baai/bge-m3")
    assert post.call_args.kwargs["headers"] == {"Authorization": "Bearer synthetic-secret"}
    assert post.call_args.kwargs["json"] == {"text": ["two"]}
    assert embeddings.embedding_model_name() == "BAAI/bge-m3"  # Existing Qdrant payload/filter identity.
    monkeypatch.setenv("CLOUDFLARE_EMBEDDING_MODEL", "@cf/custom/model")
    embeddings.embed_texts(["one"])
    assert post.call_args.args[0].endswith("/ai/run/@cf/custom/model")
    cloud.assert_not_called()


@pytest.mark.parametrize("body", [
    {"success": False}, {}, {"success": True, "result": {}},
    {"success": True, "result": {"data": [[1.] * 3]}},
    {"success": True, "result": {"data": []}},
    {"success": True, "result": {"data": [[float('nan')] * 1024]}},
])
def test_invalid_cloud_response_fails_closed(monkeypatch, cloud, body):
    response = Mock()
    response.json.return_value = body
    monkeypatch.setattr(requests, "post", Mock(return_value=response))
    with pytest.raises(embeddings.FiqhEmbeddingError, match="Cloudflare embedding request failed"):
        embeddings.embed_texts(["one"])
    cloud.assert_not_called()


@pytest.mark.parametrize("error", [requests.HTTPError, requests.Timeout, requests.ConnectionError, ValueError])
def test_cloud_errors_do_not_expose_secrets(monkeypatch, cloud, error):
    monkeypatch.setattr(requests, "post", Mock(side_effect=error("synthetic-secret")))
    with pytest.raises(embeddings.FiqhEmbeddingError) as caught:
        embeddings.embed_texts(["one"])
    assert "synthetic-secret" not in str(caught.value)
    assert caught.value.__suppress_context__
    cloud.assert_not_called()


def test_missing_credentials_and_unknown_provider(monkeypatch, cloud):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN")
    with pytest.raises(embeddings.FiqhEmbeddingError, match="incomplete"):
        embeddings.embed_texts(["one"])
    monkeypatch.setenv("EMBEDDING_PROVIDER", "unknown")
    with pytest.raises(embeddings.FiqhEmbeddingError, match="must be local or cloudflare"):
        embeddings.embed_texts(["one"])
