from unittest.mock import Mock
import pytest
from backend.pipeline import learn_pipeline as learn
from backend.pipeline import educational_pipeline as shared

QUESTIONS = [
"ما هو نظام المواريث في الإسلام؟", "ما معنى أصحاب الفروض؟", "ما معنى العصبة؟",
"ما الفرق بين الفرض والتعصيب؟", "لماذا توجد أنصبة محددة في المواريث؟",
"What is Islamic inheritance?", "What is a fixed-share heir?", "What is a residuary heir?",
"How are heirs determined in Islamic inheritance?", "Why are some inheritance shares fixed?"]

@pytest.fixture
def hit():
    return {"text": "نص تجريبي محايد لا يتضمن أحكاماً دينية. 4:12", "source": {
        "chunk_id": "neutral-record", "source_name": "Synthetic fixture", "section": "Test",
        "source_url": "https://example.invalid", "volume": 3, "page": None},
        "previous_chunk": None, "next_chunk": None}

@pytest.mark.parametrize("question", QUESTIONS)
def test_questions(question, hit, monkeypatch):
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda q, **kwargs: [hit])
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    monkeypatch.setattr(learn.provider, "explain", lambda *args: {"supported": True,
        "answer": "Neutral test explanation", "key_concepts": [], "evidence_ids": ["E1"]})
    out = learn.run_learn(question)
    assert out["decision_state"] == "ready"
    assert out["language"] == ("ar" if question in QUESTIONS[:5] else "en")
    assert len(out["source_excerpts"]) <= 2
    assert all(e["text"] in hit["text"] for e in out["source_excerpts"])


def test_empty_abstains_without_model(monkeypatch):
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda q, **kwargs: [])
    model = Mock()
    monkeypatch.setattr(learn.provider, "explain", model)
    assert learn.run_learn(QUESTIONS[0])["decision_state"] == "out_of_scope"
    model.assert_not_called()


def test_quran_backend_only(hit, monkeypatch):
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda q, **kwargs: [hit])
    model = Mock(return_value={"supported": True, "answer": "Neutral explanation",
                              "evidence_ids": ["E1"], "key_concepts": []})
    monkeypatch.setattr(learn.provider, "explain", model)
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [{"source": {
        "reference": "4:12", "source_name": "Adapter fixture", "arabic_text": "EXACT ADAPTER FIXTURE",
        "immutable_text": True}}])
    out = learn.run_learn(QUESTIONS[0])
    assert "EXACT ADAPTER FIXTURE" not in str(model.call_args)
    assert out["source_excerpts"][-1]["text"] == "EXACT ADAPTER FIXTURE"
    assert "EXACT ADAPTER FIXTURE" not in out["answer"]

@pytest.mark.parametrize("invalid", [
    {"supported": False},
    {"supported": True, "answer": "Invented", "evidence_ids": ["invented"]},
    {"supported": True, "answer": "Quoted «invented text»", "evidence_ids": ["E1"]}])
def test_unsupported_generation(hit, monkeypatch, invalid):
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda q, **kwargs: [hit])
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    monkeypatch.setattr(learn.provider, "explain", lambda *args: invalid)
    assert learn.run_learn(QUESTIONS[0])["decision_state"] == "out_of_scope"


def test_case_referral(monkeypatch):
    monkeypatch.setattr(shared, "run_pipeline", lambda q: {"decision_state": "specialist_referral",
        "result": None, "sources": [], "fiqh_evidence": []})
    out = shared.run_request("Complex unsupported case", "case")
    assert out["decision_state"] == "specialist_referral"
    assert out["case_details"]["result"] is None


def test_neighbors_exact(hit):
    hit["previous_chunk"] = {"text": "  Exact preceding text\n", "source": {**hit["source"], "chunk_id": "previous"}}
    assert learn.collect_excerpts([hit])[1]["text"] == "  Exact preceding text\n"


def test_ready_case_preserves_verified_result(monkeypatch):
    result = {"verification": {"is_consistent": True}, "shares": []}
    monkeypatch.setattr(shared, "run_pipeline", lambda q: {"decision_state": "ready",
        "result": result, "sources": [], "fiqh_evidence": []})
    out = shared.run_request("Supported case", "case")
    assert out["decision_state"] == "ready"
    assert out["case_details"]["result"] == result


def test_clarification_without_retrieval(monkeypatch):
    retrieve = Mock()
    monkeypatch.setattr(learn, "retrieve_fiqh", retrieve)
    assert learn.run_learn(" ")["decision_state"] == "needs_clarification"
    retrieve.assert_not_called()


def test_backend_ids_deduplicate_and_keep_provenance(hit):
    bundle = learn.build_evidence_bundle([hit, hit])
    assert len(bundle) == 1
    assert bundle[0]["evidence_id"] == "E1"
    assert bundle[0]["provenance"]["chunk_id"] == "neutral-record"
    assert bundle[0]["text"] == hit["text"]


def test_overlap_is_exact_slice(hit):
    first = {**hit, "text": "ABCDEFGHIJ", "source": {**hit["source"],
        "input_file": "fixture", "document_sha256": "hash", "char_start": 0, "char_end": 10}}
    second = {**hit, "text": "FGHIJKLMNO", "source": {**first["source"],
        "chunk_id": "second", "char_start": 5, "char_end": 15}}
    bundle = learn.build_evidence_bundle([first, second])
    assert [part["text"] for part in bundle] == ["ABCDEFGHIJ", "KLMNO"]
    assert bundle[1]["excerpt_char_start"] == 10


def test_inline_citations_and_english_arabic_evidence(hit, monkeypatch):
    hit = {**hit, "text": "العصبة — " + hit["text"]}
    second = {**hit, "text": "العصبة — سجل تجريبي محايد ثانٍ", "source": {**hit["source"], "chunk_id": "second"}}
    retrieve = Mock(return_value=[hit, second])
    monkeypatch.setattr(learn, "retrieve_fiqh", retrieve)
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    model = Mock(return_value={"status": "ready", "answer": "A neutral English explanation [E1] [E2]."})
    monkeypatch.setattr(learn.provider, "explain", model)
    out = learn.run_learn("What is a residuary heir?")
    assert out["decision_state"] == "ready"
    assert [e["evidence_id"] for e in out["source_excerpts"]] == ["E1", "E2"]
    assert out["source_excerpts"][0]["text"] == hit["text"]
    retrieve.assert_called_once_with(learn.educational_query("What is a residuary heir?"), top_k=3, filters={})
    assert "chunk_id" not in model.call_args.args[2][0]


@pytest.mark.parametrize("answer", ["Invented support [E99].", "No citations.", "Valid then invented [E1] [E99]."])
def test_invalid_inline_citations_fail(hit, answer):
    with pytest.raises(ValueError):
        learn.validate_citations({"status": "ready", "answer": answer}, learn.build_evidence_bundle([hit]))


def test_timeout_has_no_knowledge_fallback(hit, monkeypatch):
    import requests
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda *args, **kwargs: [hit])
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    monkeypatch.setattr(learn.provider, "explain", Mock(side_effect=requests.Timeout()))
    out = learn.run_learn("What is a residuary heir?")
    assert out["decision_state"] == "out_of_scope"
    assert any("safe fallback" in limit for limit in out["limitations"])


def test_generation_settings(hit, monkeypatch):
    from backend.llm import qwen_explainer
    post = Mock(return_value=Mock(json=lambda: {"response": '{"status":"ready","answer":"Example [E1]","key_concepts":[]}'}))
    monkeypatch.setattr(qwen_explainer.requests, "post", post)
    qwen_explainer.explain("Test", "en", learn.build_evidence_bundle([hit]))
    kwargs = post.call_args.kwargs
    assert kwargs["json"]["think"] is False
    assert kwargs["json"]["options"] == {"temperature": 0, "num_predict": 450, "num_ctx": 8192}
    assert kwargs["timeout"] == (10, 240)


def test_section_filter_uses_exact_approved_heading(monkeypatch):
    monkeypatch.setattr(learn, "load_chunks", lambda: [{"section": "إِرْثٌ "}, {"section": "أرض"}])
    assert learn.inheritance_section_filter() == {"section": "إِرْثٌ "}


def test_unknown_bare_id_fails(hit):
    with pytest.raises(ValueError, match="Unknown evidence"):
        learn.validate_citations({"answer": "Support [E1], also E99."}, learn.build_evidence_bundle([hit]))


def test_source_budget_and_one_neighbor(hit):
    previous = {"text": "P" * 200, "source": {**hit["source"], "chunk_id": "previous"}}
    following = {"text": "N" * 200, "source": {**hit["source"], "chunk_id": "next"}}
    main = {**hit, "previous_chunk": previous, "next_chunk": following}
    bundle = learn.build_evidence_bundle([main], max_characters=220)
    assert sum(len(e["text"]) for e in bundle) == 220
    assert bundle[0]["text"] == previous["text"]
    assert not any(e["provenance"]["chunk_id"] == "next" for e in bundle)


def test_comparison_splits_three_hit_budget(monkeypatch):
    retrieve = Mock(return_value=[])
    monkeypatch.setattr(learn, "retrieve_fiqh", retrieve)
    learn.retrieve_educational_evidence("ما الفرق بين الفرض والتعصيب؟")
    assert [call.kwargs["top_k"] for call in retrieve.call_args_list] == [2, 1]


def test_neighbor_paragraph_keeps_original_provenance(hit):
    text = "Earlier neutral paragraph.\n\nUseful neighboring paragraph.\n\n"
    source = {**hit["source"], "chunk_id": "previous", "char_start": 100, "char_end": 100 + len(text)}
    main = {**hit, "previous_chunk": {"text": text, "source": source}}
    bundle = learn.build_evidence_bundle([main])
    first = bundle[0]
    assert first["text"] == "Useful neighboring paragraph."
    assert first["provenance"] == source
    assert first["excerpt_char_start"] == 100 + text.index("Useful")
    assert first["excerpt_char_end"] - first["excerpt_char_start"] == len(first["text"])


def test_timeout_can_use_source_bound_concept_metadata(hit, monkeypatch):
    import requests
    from backend.rules import educational_concepts as catalogue
    monkeypatch.setattr(catalogue, "CONCEPTS", ({"concept_id": "neutral", "queries": ("neutral",),
        "anchors": ("neutral fixture",), "en": {"term": "Neutral", "explanation": "Neutral fixture explanation."}},))
    hit = {**hit, "text": "Exact neutral fixture record."}
    monkeypatch.setattr(learn, "retrieve_fiqh", lambda *args, **kwargs: [hit])
    monkeypatch.setattr(learn, "enrich_sources", lambda rules: [])
    monkeypatch.setattr(learn.provider, "explain", Mock(side_effect=requests.Timeout()))
    out = learn.run_learn("Explain neutral")
    assert out["decision_state"] == "ready"
    assert out["answer"] == "Neutral fixture explanation. [E1]"
    assert out["source_excerpts"][0]["text"] == hit["text"]


def test_concept_requires_all_source_anchors(monkeypatch):
    from backend.rules import educational_concepts as catalogue
    monkeypatch.setattr(catalogue, "CONCEPTS", ({"concept_id": "neutral", "queries": ("neutral",),
        "anchors": ("first", "second"), "en": {"term": "Neutral", "explanation": "Neutral explanation."}},))
    assert catalogue.supported_concepts("neutral", "en", [{"evidence_id": "E1", "text": "first"}]) == []
