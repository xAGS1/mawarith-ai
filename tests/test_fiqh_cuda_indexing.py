import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from backend.rag.fiqh import embeddings, vector_store
from backend.rag.fiqh.chunker import chunk_record
from backend.rag.fiqh.schemas import PUBLISHER, SOURCE_NAME


@pytest.mark.parametrize("available,device", [(True, "cuda"), (False, "cpu")])
def test_device_selection(available, device, monkeypatch):
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: available)))
    assert embeddings.select_embedding_device() == device


@pytest.mark.parametrize("device", ["cuda", "cpu"])
def test_model_uses_selected_device_and_modern_dimension_api(device, monkeypatch, capsys):
    model = Mock()
    model.get_embedding_dimension.return_value = embeddings.DIMENSION
    constructor = Mock(return_value=model)
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=constructor))
    embeddings._load_model.cache_clear()
    with patch.object(embeddings, "select_embedding_device", return_value=device):
        try:
            assert embeddings._load_model("test-model") is model
        finally:
            embeddings._load_model.cache_clear()
    assert constructor.call_args.kwargs["device"] == device
    model.get_sentence_embedding_dimension.assert_not_called()
    assert model.half.call_count == (1 if device == "cuda" else 0)
    assert f"Embedding device: {device}" in capsys.readouterr().out


def test_cuda_failure_does_not_retry_cpu(monkeypatch):
    constructor = Mock(side_effect=RuntimeError("CUDA initialization failed"))
    monkeypatch.setitem(sys.modules, "sentence_transformers", SimpleNamespace(SentenceTransformer=constructor))
    embeddings._load_model.cache_clear()
    with patch.object(embeddings, "select_embedding_device", return_value="cuda"):
        with pytest.raises(embeddings.FiqhEmbeddingError, match="no CPU fallback"):
            embeddings._load_model("test-model")
    assert constructor.call_count == 1


def test_encoder_batching_preserves_output_count(monkeypatch):
    monkeypatch.setenv("FIQH_EMBEDDING_BATCH_SIZE", "32")
    model = Mock()
    model.encode.side_effect = lambda texts, **kwargs: SimpleNamespace(tolist=lambda: [[1.0] * embeddings.DIMENSION for _ in texts])
    with patch.object(embeddings, "_load_model", return_value=model):
        assert len(embeddings.embed_texts(["نص اختبار محايد."] * 35)) == 35
    assert model.encode.call_args.kwargs["batch_size"] == 32


def test_batch_setting_validation(monkeypatch):
    monkeypatch.setenv("FIQH_EMBEDDING_BATCH_SIZE", "16")
    assert embeddings.embedding_batch_size() == 16
    monkeypatch.setenv("FIQH_EMBEDDING_BATCH_SIZE", "bad")
    with pytest.raises(embeddings.FiqhEmbeddingError):
        embeddings.embedding_batch_size()


def test_deterministic_ids():
    assert vector_store.point_id("chunk-1") == vector_store.point_id("chunk-1")
    assert vector_store.point_id("chunk-1") != vector_store.point_id("chunk-2")


def test_interrupted_index_rerun_upserts_same_ids_and_batches(capsys):
    chunks = []
    for index in range(5):
        chunks.extend(chunk_record({"source_type": "fiqh", "source_name": SOURCE_NAME, "publisher": PUBLISHER,
                                   "topic": "اختبار محايد", "volume": None, "page": None, "section": None,
                                   "text": f"ترتيب رفوف اختبار {index}. " * 8, "source_url": "https://example.invalid/test",
                                   "verified_source": True}, "synthetic.json"))
    points = {vector_store.point_id(chunks[0]["chunk_id"]): {}}  # One preexisting point.
    batches = []
    def request(self, method, path, body=None):
        if "points?" in path:
            batches.append(len(body["points"]))
            points.update({p["id"]: p for p in body["points"]})
            return {}
        if path.endswith("/count"):
            return {"count": len(points)}
        raise AssertionError(path)
    with (
        patch.object(vector_store, "load_chunks", return_value=chunks + [chunks[0]]),
        patch.object(vector_store.QdrantFiqhStore, "ensure_collection"),
        patch.object(vector_store.QdrantFiqhStore, "_request", request),
        patch.object(vector_store, "embed_texts", side_effect=lambda texts, **kwargs: [[1.0] * embeddings.DIMENSION for _ in texts]),
    ):
        assert vector_store.index_chunks(batch_size=2) == 5
        assert vector_store.index_chunks(batch_size=2) == 5
    assert len(points) == 5
    assert batches == [2, 2, 1, 2, 2, 1]
    output = capsys.readouterr().out
    assert "Embedding batch 3/3" in output
    assert "Upserted 5/5" in output
    assert "Qdrant points_count: 5" in output
