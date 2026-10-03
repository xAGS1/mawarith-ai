"""All text fixtures are synthetic neutral Arabic, never religious excerpts."""

import copy
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from pydantic import ValidationError

from backend.pipeline.qwen_pipeline import run_pipeline
from backend.rag.fiqh.chunker import chunk_record, estimate_tokens
from backend.rag.fiqh.embeddings import DIMENSION, FiqhEmbeddingError, embed_texts, validate_vectors
from backend.rag.fiqh.loader import ingest, load_source_file
from backend.rag.fiqh.retriever import retrieve_fiqh
from backend.rag.fiqh.schemas import FiqhSourceRecord, PUBLISHER, SOURCE_NAME
from backend.rag.fiqh.vector_store import FiqhStoreError, QdrantFiqhStore, build_filter, build_payload, index_chunks


TEXT = "هذا نص تجريبي محايد عن ترتيب الكتب وألوان الرفوف.\r\n\r\nوهذه فقرة اختبار ثانية.\u00a0\n"


def record(text=TEXT):
    return {"source_type": "fiqh", "source_name": SOURCE_NAME, "publisher": PUBLISHER,
            "topic": "اختبار اصطناعي محايد", "volume": None, "page": None, "section": None,
            "text": text, "source_url": "https://example.invalid/synthetic-test-only",
            "verified_source": True}


def chunk():
    return chunk_record(record(), "synthetic.json")[0]


@pytest.mark.parametrize("missing", ["source_name", "publisher", "topic", "volume", "page", "section", "source_url", "verified_source"])
def test_source_metadata_required(missing):
    source = record()
    del source[missing]
    with pytest.raises(ValidationError):
        FiqhSourceRecord.model_validate(source)


@pytest.mark.parametrize("changes", [{"verified_source": False}, {"verified_source": 1},
                                     {"source_name": "unapproved"}, {"publisher": "unknown"},
                                     {"source_url": "invented"}, {"text": "   "}])
def test_unapproved_or_invalid_source_rejected(changes):
    source = record()
    source.update(changes)
    with pytest.raises(ValidationError):
        FiqhSourceRecord.model_validate(source)


@pytest.mark.parametrize("suffix", [".txt", ".md"])
def test_loader_preserves_exact_utf8_text(suffix, tmp_path):
    source = tmp_path / ("synthetic" + suffix)
    source.write_bytes(TEXT.encode("utf-8"))
    metadata = record()
    del metadata["text"]
    source.with_name(source.name + ".metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    assert load_source_file(source)[0]["text"] == TEXT


@pytest.mark.parametrize("as_list", [False, True])
def test_json_loader(as_list, tmp_path):
    source = tmp_path / "synthetic.json"
    source.write_text(json.dumps([record()] if as_list else record()), encoding="utf-8")
    assert load_source_file(source)[0]["text"] == TEXT


def test_missing_sidecar_rejected(tmp_path):
    source = tmp_path / "synthetic.txt"
    source.write_text(TEXT, encoding="utf-8")
    with pytest.raises(ValueError, match="sidecar"):
        load_source_file(source)


def test_empty_corpus_ignores_readme_and_produces_empty_artifact(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "README.md").write_text("Not source content", encoding="utf-8")
    output = tmp_path / "processed" / "chunks.json"
    assert ingest(raw, output) == 0
    assert json.loads(output.read_text()) == []


def test_ingestion_retains_provenance_and_does_not_ingest_sidecar(tmp_path):
    source = tmp_path / "synthetic.txt"
    source.write_bytes(TEXT.encode("utf-8"))
    metadata = record()
    del metadata["text"]
    source.with_name(source.name + ".metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    output = tmp_path.parent / (tmp_path.name + "-chunks.json")
    assert ingest(tmp_path, output) == 1
    result = json.loads(output.read_text(encoding="utf-8"))[0]
    assert result["text"] == TEXT
    assert result["publisher"] == PUBLISHER


def test_chunking_is_exact_with_overlap_and_full_coverage():
    text = ("هذه فقرة اصطناعية عن ألوان الرفوف وترتيب الكتب. " * 70 + "\n\n") * 4
    source = record(text)
    original = copy.deepcopy(source)
    chunks = chunk_record(source, "synthetic.txt")
    assert source == original
    assert len(chunks) > 1
    assert chunks[0]["char_start"] == 0 and chunks[-1]["char_end"] == len(text)
    for part in chunks:
        assert part["text"] == text[part["char_start"]:part["char_end"]]
        assert estimate_tokens(part["text"]) <= 700
        assert part["verified_source"] is True
        assert part["source_url"] == source["source_url"]
    for first, second in zip(chunks, chunks[1:]):
        assert first["char_start"] < second["char_start"] < first["char_end"]
        overlap = text[second["char_start"]:first["char_end"]]
        assert 60 <= estimate_tokens(overlap) <= 100
    assert chunks == chunk_record(source, "synthetic.txt")


def test_short_paragraphs_are_not_mutated():
    assert chunk_record(record(), "synthetic.txt")[0]["text"] == TEXT


def test_embedding_dimension_and_counts():
    assert validate_vectors([[1.0] * DIMENSION], 1)[0] == [1.0] * DIMENSION
    for vectors, count in [([[1.0] * 3], 1), ([[1.0] * DIMENSION], 2), ([[float("nan")] * DIMENSION], 1)]:
        with pytest.raises(FiqhEmbeddingError):
            validate_vectors(vectors, count)


def test_embedding_wrapper_is_local_and_preserves_input():
    model = Mock()
    model.encode.return_value.tolist.return_value = [[1.0] * DIMENSION]
    with patch("backend.rag.fiqh.embeddings._load_model", return_value=model):
        assert len(embed_texts([TEXT])[0]) == DIMENSION
    assert model.encode.call_args.args[0] == [TEXT]


def test_qdrant_payload_contains_full_exact_provenance():
    part = chunk()
    payload = build_payload(part)
    assert all(payload[k] == v for k, v in part.items())
    assert payload["embedding_model"] == "BAAI/bge-m3"
    assert payload["text"] == TEXT


def test_qdrant_index_and_query_rest_payloads():
    calls = []
    def request(method, url, json=None, timeout=None):
        calls.append((method, url, json))
        result = {"collections": [{"name": "mawarith_fiqh"}]} if url.endswith("/collections") else {}
        if method == "GET" and url.endswith("/mawarith_fiqh"):
            result = {"config": {"params": {"vectors": {"size": DIMENSION, "distance": "Cosine"}}}}
        if method == "POST":
            result = {"points": []}
        response = Mock()
        response.json.return_value = {"status": "ok", "result": result}
        return response
    with patch("backend.rag.fiqh.vector_store.requests.request", side_effect=request):
        store = QdrantFiqhStore()
        store.ensure_collection()
        store.upsert([chunk()], [[1.0] * DIMENSION])
        assert store.query([1.0] * DIMENSION, filters={"topic": "اختبار", "volume": 2}) == []
    upsert = next(body for method, url, body in calls if method == "PUT")
    assert upsert["points"][0]["payload"]["text"] == TEXT
    query = calls[-1][2]
    assert {"key": "volume", "match": {"value": 2}} in query["filter"]["must"]


def test_qdrant_failure_has_no_fallback():
    with patch("backend.rag.fiqh.vector_store.requests.request", side_effect=requests.ConnectionError("offline")):
        with pytest.raises(FiqhStoreError, match="Qdrant request failed"):
            QdrantFiqhStore().connect()


def test_incompatible_qdrant_dimensions_rejected():
    store = QdrantFiqhStore()
    with (
        patch.object(store, "connect", return_value=["mawarith_fiqh"]),
        patch.object(store, "_request", return_value={"config": {"params": {"vectors": {"size": 3, "distance": "Cosine"}}}}),
        pytest.raises(FiqhStoreError, match="incompatible"),
    ):
        store.ensure_collection()


def test_chunk_offsets_cannot_be_fabricated():
    part = chunk()
    part["char_end"] += 1
    with pytest.raises(ValidationError):
        build_payload(part)


def test_filter_support_and_invalid_filter():
    assert len(build_filter({"topic": "x", "source_name": SOURCE_NAME, "section": None, "volume": 1})["must"]) == 9
    with pytest.raises(ValueError):
        build_filter({"unapproved_field": 1})


def test_empty_corpus_does_not_contact_qdrant_or_load_model(tmp_path):
    with (
        patch("backend.rag.fiqh.retriever.load_chunks", return_value=[]),
        patch("backend.rag.fiqh.retriever.QdrantFiqhStore") as store,
        patch("backend.rag.fiqh.retriever.embed_texts") as embed,
    ):
        assert retrieve_fiqh("اختبار") == []
    store.assert_not_called()
    embed.assert_not_called()
    assert index_chunks(tmp_path / "missing.json") == 0


@pytest.mark.parametrize("hits", [False, True])
def test_retrieval_returns_exact_approved_text_or_empty(hits):
    part = chunk()
    store = Mock()
    store.query.return_value = [{"score": 0.82, "payload": build_payload(part)}] if hits else []
    with (
        patch("backend.rag.fiqh.retriever.load_chunks", return_value=[part]),
        patch("backend.rag.fiqh.retriever.QdrantFiqhStore", return_value=store),
        patch("backend.rag.fiqh.retriever.embed_texts", return_value=[[1.0] * DIMENSION]),
    ):
        evidence = retrieve_fiqh("اختبار", filters={"topic": "اختبار"})
    assert evidence == ([{"score": 0.82, "text": TEXT, "source": {k: v for k, v in part.items() if k != "text"}}] if hits else [])


def test_tampered_qdrant_text_rejected():
    part = chunk()
    payload = build_payload(part)
    payload["text"] = "محتوى اصطناعي معدل"
    store = Mock()
    store.query.return_value = [{"score": 1.0, "payload": payload}]
    with (
        patch("backend.rag.fiqh.retriever.load_chunks", return_value=[part]),
        patch("backend.rag.fiqh.retriever.QdrantFiqhStore", return_value=store),
        patch("backend.rag.fiqh.retriever.embed_texts", return_value=[[1.0] * DIMENSION]),
        pytest.raises(FiqhStoreError, match="approved"),
    ):
        retrieve_fiqh("اختبار")


def test_rag_evidence_cannot_promote_unsupported_relation():
    parsed = {"mentioned_relatives": [{"relation": "أخ شقيق", "count": 1}]}
    evidence = [{"score": 0.82, "text": TEXT, "source": {"source_type": "fiqh"}}]
    with (
        patch("backend.pipeline.qwen_pipeline.parse_relations", return_value=parsed),
        patch("backend.pipeline.qwen_pipeline.enrich_sources", side_effect=lambda r: r),
        patch("backend.pipeline.qwen_pipeline.retrieve_fiqh", return_value=evidence),
        patch("backend.pipeline.qwen_pipeline.analyze_case") as reasoner,
    ):
        output = run_pipeline("اختبار محايد")
    assert output["fiqh_evidence"] == evidence
    assert output["decision_state"] == "insufficient_sources"
    assert output["result"] is None
    reasoner.assert_not_called()


def test_pipeline_reports_qdrant_unavailability_explicitly():
    with (
        patch("backend.pipeline.qwen_pipeline.parse_relations", return_value={"mentioned_relatives": []}),
        patch("backend.pipeline.qwen_pipeline.retrieve_fiqh", side_effect=FiqhStoreError("Qdrant offline")),
    ):
        output = run_pipeline("اختبار")
    assert output["fiqh_evidence"] == []
    assert output["fiqh_retrieval"] == {"status": "unavailable", "error": "Qdrant offline"}
