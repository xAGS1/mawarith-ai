"""Optional curriculum context enriches the existing RAG, not the solver."""
import hashlib
import json
from pathlib import Path
from unittest.mock import Mock
from fastapi.testclient import TestClient
from backend import app as api
from backend.llm import qwen_understanding
from backend.pipeline import educational_pipeline, rag_answer
from backend.pipeline.semantic_request import SemanticRequest

TRANSPORT = qwen_understanding.understand_input
CONTEXT = {"slug": "awl", "title": "العول"}
REQUEST = {"intent": "educational", "language": "ar", "topic": "العول والرد",
    "retrieval_query": "العول والرد", "concepts": ["العول", "الرد"], "case": None, "clarification_question": None}

def test_context_reaches_understanding_retrieval_and_grounded_explanation(monkeypatch):
    understand = Mock(return_value=REQUEST)
    monkeypatch.setattr(qwen_understanding, "understand_input", understand)
    text = "العول زيادة في الفروض ينتج عنها زيادة في أصل المسألة."
    evidence = [{"evidence_id": "E1", "text": text, "source_name": "Fixture",
        "provenance": {"source_name": "Fixture", "source_id": "fixture"}}]
    retrieve = Mock(return_value=evidence)
    generate = Mock(return_value={"status": "ready", "answer": text + " [E1]", "evidence_ids": ["E1"]})
    monkeypatch.setattr(rag_answer, "retrieve_context", retrieve)
    monkeypatch.setattr(rag_answer.provider, "explain_context", generate)
    answer = educational_pipeline.run_request("ليش يصير كذا؟", "learn", concept_context=CONTEXT)
    assert answer["evidence_status"] == "supported"
    assert understand.call_args.args[0] == "ليش يصير كذا؟"
    assert understand.call_args.kwargs["concept_context"] == CONTEXT
    assert retrieve.call_args.args[0] == "ليش يصير كذا؟"
    search = retrieve.call_args.args[1]
    assert "الرد" in search.retrieval_query and "العول" in search.retrieval_query
    payload = json.loads(generate.call_args.args[0])
    assert payload["question"] == "ليش يصير كذا؟" and payload["current_concept"] == CONTEXT
    assert "current_concept" not in answer

def test_context_is_prompt_data_not_source_or_filter(monkeypatch):
    response = Mock()
    response.json.return_value = {"response": json.dumps(REQUEST)}
    post = Mock(return_value=response)
    monkeypatch.setattr(qwen_understanding.requests, "post", post)
    TRANSPORT("وش الفرق بينه وبين الرد؟", SemanticRequest.model_json_schema(), concept_context=CONTEXT)
    payload = post.call_args.kwargs["json"]
    assert json.loads(payload["prompt"])["current_concept"] == CONTEXT
    assert "not an answer or a source" in payload["system"]
    assert "do not restrict retrieval" in payload["system"]

def test_optional_api_context_preserves_existing_contract(monkeypatch):
    result = {"mode": "learn", "decision_state": "ready", "language": "ar", "answer": "Fixture"}
    run = Mock(return_value=result)
    monkeypatch.setattr(api, "run_request", run)
    client = TestClient(api.app)
    assert client.post("/ask", json={"mode": "learn", "question": "why", "concept_context": CONTEXT}).status_code == 200
    assert run.call_args.kwargs == {"concept_context": CONTEXT}
    client.post("/ask", json={"mode": "case", "question": "case", "concept_context": CONTEXT})
    assert run.call_args.kwargs == {}
    client.post("/ask", json={"mode": "learn", "question": "plain"})
    assert run.call_args.kwargs == {}
    assert client.post("/ask", json={"question": "why", "concept_context": {**CONTEXT, "instructions": "extra"}}).status_code == 422

def test_curriculum_quotes_have_integrity_and_no_private_paths():
    path = Path("frontend/src/data/concept-evidence.json")
    data = json.loads(path.read_text(encoding="utf8"))
    assert len(data) == 8  # Seven concepts and the separately sourced awl example.
    for source in data.values():
        assert hashlib.sha256(source["text"].encode()).hexdigest() == source["excerpt_sha256"]
        assert len(source["text"]) < 700 and source["chunk_id"]
        assert not ({"local_source", "input_file", "repository_file"} & source.keys())
    original = json.loads(Path("backend/learning/curated_source_passages.json").read_text(encoding="utf8"))
    assert data["awl-example"]["text"] == original["awl"]["properties"]["origin_24_example"]["text"]
    assert data["fixed-share-heirs"]["text"] == original["fixed_share_heirs"]["text"]
