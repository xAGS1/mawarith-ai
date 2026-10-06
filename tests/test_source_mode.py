import hashlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend.rag import source_mode, educational_context, dorar_retrieval
from backend.rag.fiqh import retriever
from backend.rag.fiqh.schemas import SOURCE_NAME, PUBLISHER


def fiqh_payload():
    text = "synthetic source text " * 8
    return {"text": text, "source_type": "fiqh", "source_name": SOURCE_NAME,
            "publisher": PUBLISHER, "topic": "synthetic", "volume": 3,
            "section": "synthetic", "page": None, "source_url": "https://example.invalid/source",
            "verified_source": True, "chunk_id": "test-chunk", "document_sha256": "a" * 64,
            "input_file": "test.json", "char_start": 0, "char_end": len(text),
            "embedding_model": "BAAI/bge-m3"}


@pytest.mark.parametrize("mode", [None, "local", "cloud"])
def test_fiqh_modes_preserve_validation_without_cloud_files(monkeypatch, mode):
    monkeypatch.delenv("SOURCE_MODE", raising=False)
    if mode:
        monkeypatch.setenv("SOURCE_MODE", mode)
    payload = fiqh_payload()
    chunk = {k:v for k,v in payload.items() if k != "embedding_model"}
    loader = Mock(side_effect=AssertionError("Must not read local files")) if mode == "cloud" else Mock(return_value=[chunk])
    monkeypatch.setattr(retriever, "load_chunks", loader)
    store = Mock()
    store.query.return_value = [{"payload": payload, "score": .8}]
    monkeypatch.setattr(retriever, "QdrantFiqhStore", Mock(return_value=store))
    monkeypatch.setattr(retriever, "embed_texts", lambda _: [[1.] * 1024])
    result = retriever.retrieve_fiqh("synthetic", semantic_only=True)
    assert result[0]["text"] == chunk["text"]
    assert result[0]["score"] == .8
    assert result[0]["previous_chunk"] is None
    assert loader.call_count == (0 if mode == "cloud" else 1)
    payload["verified_source"] = False
    with pytest.raises(retriever.FiqhStoreError):
        retriever.retrieve_fiqh("synthetic", semantic_only=True)


def educational_record():
    text = "synthetic direct definition"
    return {"text": text, "source": {"source_id": "uqu_mawarith_1", "source_name": "UQU",
            "source_type": "educational_reference", "verified_source": True, "retrieval_eligible": True,
            "page": 13, "chunk_id": "test", "document_sha256": "a"*64,
            "excerpt_sha256": hashlib.sha256(text.encode()).hexdigest()}, "embedding_model": "BAAI/bge-m3"}


def test_uqu_cloud_payload_and_hash_validation(monkeypatch):
    from backend.rag.fiqh import embeddings, vector_store
    payload = educational_record()
    store = Mock()
    store._request.return_value = {"points": [{"payload": payload, "score": .9}]}
    constructor = Mock(return_value=store)
    monkeypatch.setattr(vector_store, "QdrantFiqhStore", constructor)
    monkeypatch.setattr(embeddings, "embed_texts", lambda _: [[1.] * 1024])
    result = source_mode.cloud_candidates("synthetic", "mawarith_uqu", 2, source_id="uqu_mawarith_1")
    assert result[0]["source"]["page"] == 13
    assert result[0]["score"] == .9
    constructor.assert_called_once_with(collection="mawarith_uqu")
    payload["text"] += "tampered"
    with pytest.raises(ValueError, match="checksum"):
        source_mode.cloud_candidates("synthetic", "mawarith_uqu", 2, source_id="uqu_mawarith_1")


@pytest.mark.parametrize("mode", ["local", "cloud"])
def test_educational_source_routing_no_cloud_corpus_reads(monkeypatch, mode):
    monkeypatch.setenv("SOURCE_MODE", mode)
    source = educational_record()
    record = {"text": source["text"], "source": source["source"], "score": .9}
    local_uqu = Mock(side_effect=AssertionError("local UQU accessed")) if mode == "cloud" else Mock(return_value=[])
    local_quran = Mock(side_effect=AssertionError("local Quran accessed")) if mode == "cloud" else Mock(return_value=[])
    monkeypatch.setattr(educational_context, "uqu_records", local_uqu)
    monkeypatch.setattr(educational_context, "quran_records", local_quran)
    cloud = Mock(side_effect=lambda q,c,k,**kw: [record] if c == "mawarith_uqu" else [])
    monkeypatch.setattr(educational_context, "cloud_candidates", cloud)
    monkeypatch.setattr(educational_context, "retrieve_fiqh", lambda *a,**kw: [])
    monkeypatch.setattr(educational_context, "dorar_candidates", lambda *a,**kw: [])
    result = educational_context.retrieve_context("synthetic", SimpleNamespace(retrieval_query="synthetic", concepts=[]))
    assert bool(result) == (mode == "cloud")
    assert local_uqu.call_count == local_quran.call_count == (0 if mode == "cloud" else 1)
    assert cloud.call_count == (2 if mode == "cloud" else 0)


def test_dorar_cloud_does_not_load_corpus(monkeypatch):
    monkeypatch.setenv("SOURCE_MODE", "cloud")
    payload = educational_record()
    payload["source"].update(source_id="dorar_fiqhia", source_name="Dorar", source_type="fiqh_reference",
        book="\u0643\u062a\u0627\u0628 \u0627\u0644\u0645\u0648\u0627\u0631\u064a\u062b", content_kind="definition")
    store = Mock()
    store._request.return_value = {"points": [{"payload": payload, "score": .8}]}
    monkeypatch.setattr(dorar_retrieval, "QdrantFiqhStore", Mock(return_value=store))
    loader = Mock(side_effect=AssertionError("Local corpus accessed"))
    monkeypatch.setattr(dorar_retrieval, "load_dorar_chunks", loader)
    monkeypatch.setattr(dorar_retrieval, "embed_texts", lambda _: [[1.] * 1024])
    assert dorar_retrieval.dorar_candidates("synthetic", "synthetic")[0]["text"] == payload["text"]
    loader.assert_not_called()


def test_invalid_source_mode_fails_closed(monkeypatch):
    monkeypatch.setenv("SOURCE_MODE", "invalid")
    with pytest.raises(ValueError, match="SOURCE_MODE"):
        source_mode.cloud_sources()
