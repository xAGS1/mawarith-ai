"""Semantic orchestration and source-grounding without phrase-specific routes."""
from copy import deepcopy
from unittest.mock import Mock
import pytest
from backend.pipeline import educational_pipeline as main
from backend.pipeline import rag_answer
from backend.pipeline.semantic_request import SemanticRequest, understand_request
from backend.pipeline.educational_claims import filter_claims, filter_calculation_prose
from backend.llm import qwen_understanding
from backend.pipeline import qwen_pipeline as cases
from backend.rag.retriever import retrieve_rules
from backend.rules.case_features import build_case_features
from backend.rules.distribution import allocate
from backend.rag import educational_context as context

LEARN = ["ما معنى العصبة؟", "ايش هي العول؟", "وش يعني الرد؟", "فهمني الحجب", "اشرح لي أصحاب الفروض", "وش الفرق بين الفرض والتعصيب؟", "كيف يشتغل العول؟"]
CALCULATE = ["مات وترك ابنان فقط", "واحد توفى وترك زوجة وولد", "توفي رجل وترك زوجة وأم وابنين وبنت", "لو مات وترك بنت وأخ وش يصير؟"]


def understanding(intent="educational", counts=None):
    return {"intent": intent, "language": "ar", "topic": "Neutral test topic",
        "retrieval_query": "Neutral semantic query", "concepts": [],
        "case": {"heirs": [{"relation": r, "count": n} for r,n in counts.items()], "relationships": list(counts), "counts": counts} if counts is not None else None,
        "clarification_question": None}


def evidence(text="Neutral exact supporting context.", id="E1"):
    return {"evidence_id": id, "text": text, "source_name": "Fixture source", "section": "Fixture",
        "provenance": {"source_name": "Fixture source", "source_id": "fixture", "source_type": "fiqh"},
        "immutable_text": True, "internal_provenance": {"chunk_id": "PRIVATE_HASH"}}


@pytest.mark.parametrize("question", LEARN)
def test_natural_educational_variations_use_semantics(question, monkeypatch):
    classifier = Mock(return_value=understanding())
    monkeypatch.setattr(qwen_understanding, "understand_input", classifier)
    retrieve = Mock(return_value=[evidence('A naturally phrased educational explanation.')])
    monkeypatch.setattr(rag_answer, "retrieve_context", retrieve)
    monkeypatch.setattr(rag_answer.provider, "explain_context", Mock(return_value={
        "status": "ready", "answer": "A naturally phrased educational explanation [E1].", "key_concepts": []}))
    response = main.run_request(question, "case")  # A mismatched hint cannot force a calculation.
    assert response["mode"] == "learn" and response["evidence_status"] == "supported"
    assert "[E1]" not in response["answer"] and "PRIVATE_HASH" not in str(response)
    classifier.assert_called_once()
    assert retrieve.call_args.args[1].retrieval_query == "Neutral semantic query"


@pytest.mark.parametrize("question", CALCULATE)
def test_calculation_semantic_facts_sent_to_solver(question, monkeypatch):
    facts = {"ابن": 2}
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=understanding("calculation", facts)))
    # The source-backed generic sons family now covers these mocked parsed facts.
    monkeypatch.setattr(cases, "parse_relations", Mock(side_effect=AssertionError("Second extraction call")))
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda _: [])
    monkeypatch.setattr(cases, "enrich_sources", lambda x: x)
    reasoner = Mock(side_effect=AssertionError("LLM must never calculate"))
    monkeypatch.setattr(cases, "analyze_case", reasoner)
    monkeypatch.setattr(main.provider, "explain_context", Mock(return_value={"status": "insufficient", "answer": ""}))
    result = main.run_request(question, "learn")
    assert result["mode"] == "case"
    if question == CALCULATE[-1]:
        assert result["decision_state"] == "needs_clarification"
        assert result["case_details"]["result"] is None
    else:
        assert result["decision_state"] == "ready"
        distribution = result["case_details"]["result"]["post_tasil"]["distribution"]
        assert [(r["heir"], r["count"], r["per_head_shares"]) for r in distribution] == [("ابن", 2, "1/2")]
    reasoner.assert_not_called()


def test_verified_calculation_is_immutable_to_explainer(monkeypatch):
    facts = {"زوجة": 1, "أم": 1, "ابن": 2, "بنت": 1}
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=understanding("calculation", facts)))
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda _: [])
    monkeypatch.setattr(cases, "enrich_sources", lambda x: x)
    model = Mock(return_value={"status": "ready", "answer": "الزوجة تأخذ 1/2 [E1]."})
    monkeypatch.setattr(main.provider, "explain_context", model)
    response = main.run_request(CALCULATE[2])
    parsed = {"mentioned_relatives": [{"relation": r, "count": n} for r,n in facts.items()]}
    expected = allocate(parsed, retrieve_rules(parsed, build_case_features(parsed)))
    assert response["case_details"]["result"] == expected
    assert response["decision_state"] == "ready"
    assert "1/2" not in response["answer"]
    assert expected["verification"]["is_consistent"]
    assert model.call_args.args[-1] == expected


def test_ambiguous_sibling_requires_deterministic_clarification(monkeypatch):
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=understanding("calculation", {"بنت": 1, "أخ": 1})))
    monkeypatch.setattr(cases, "retrieve_fiqh", lambda _: [])
    monkeypatch.setattr(cases, "enrich_sources", lambda x: x)
    result = main.run_request(CALCULATE[-1])
    assert result["decision_state"] == "needs_clarification"
    assert result["case_details"]["result"] is None


def test_paraphrase_allowed_optional_unsupported_claim_removed(monkeypatch):
    text = "للبنت الواحدة النصف عند عدم وجود ابن."
    monkeypatch.setattr(rag_answer, "retrieve_context", lambda *args: [evidence(text)])
    monkeypatch.setattr(rag_answer.provider, "explain_context", lambda *args: {"status": "ready",
        "answer": "يكون نصيب البنت الواحدة النصف عندما لا يوجد ابن [E1].\nالأخ يأخذ الباقي [E1]."})
    response = rag_answer.answer_educational("اشرح الحالة", SemanticRequest.model_validate(understanding()))
    assert response["evidence_status"] == "supported"
    assert "يكون نصيب" in response["answer"]
    assert "الأخ" not in response["answer"]
    assert response["source_excerpts"][0]["text"] == text


def test_no_evidence_no_model(monkeypatch):
    monkeypatch.setattr(rag_answer, "retrieve_context", lambda *args: [])
    model = Mock()
    monkeypatch.setattr(rag_answer.provider, "explain_context", model)
    assert rag_answer.answer_educational("unknown", SemanticRequest.model_validate(understanding()))["evidence_status"] == "insufficient"
    model.assert_not_called()


def test_invalid_schema_no_shares_allowed(monkeypatch):
    bad = understanding("calculation", {"ابن": 2})
    bad["case"]["fractions"] = ["1/2"]
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(return_value=bad))
    assert understand_request("question") is None


def test_multisource_context_preserves_original_query_and_exact_text(monkeypatch):
    texts = ["EXACT UQU text", "EXACT Quran text"]
    monkeypatch.setattr(context, "uqu_records", lambda: [{"text": texts[0], "source": {"source_name": "UQU", "source_type": "educational_reference"}}])
    monkeypatch.setattr(context, "quran_records", lambda: [{"text": texts[1], "source": {"source_name": "Quran", "source_type": "quran"}}])
    monkeypatch.setattr(context, "semantic_candidates", lambda query, records, k: [{**r, "score": 0.8} for r in records])
    fiqh = Mock(return_value=[{"text": "EXACT Fiqh text", "score": 0.9, "source": {"source_name": "Fiqh", "source_type": "fiqh", "input_file": "SECRET"}}])
    monkeypatch.setattr(context, "retrieve_fiqh", fiqh)
    results = context.retrieve_context("Original question", SemanticRequest.model_validate(understanding()))
    assert len(results) == 3
    assert "Original question" in fiqh.call_args.args[0]
    assert fiqh.call_args.kwargs["semantic_only"]
    assert {r["text"] for r in results} == {*texts, "EXACT Fiqh text"}
    assert "SECRET" not in str([r["provenance"] for r in results])


def test_allocator_rejects_missing_executable_coverage():
    with pytest.raises(ValueError):
        allocate({"mentioned_relatives": [{"relation": "ابن", "count": 2}]}, [])


def test_invalid_citation_not_accepted():
    answer, blocked = filter_claims("An invented claim [E99].", [evidence()])
    assert not answer and blocked


def test_verified_fraction_may_be_explained_but_not_changed():
    result = {"shares": [{"heir": "زوجة", "fraction": "1/8"}],
              "post_tasil": {"distribution": [{"heir": "زوجة", "per_head_shares": "1/8"}]}}
    assert "1/8" in filter_calculation_prose("الزوجة تأخذ 1/8 [E1].", result)
    for wrong in ["1/2", "1/0", "-1/8", "0.5", "50%"]:
        assert not filter_calculation_prose("الزوجة تأخذ " + wrong + " [E1].", result)


def test_declared_citations_support_paraphrase_without_exposing_ids():
    answer, blocked = filter_claims("A naturally phrased explanation.", [evidence()], ["E1"])
    assert answer and not blocked
    assert not filter_claims("A naturally phrased explanation.", [evidence()], ["E99"])[0]


def test_count_index_is_derived_from_strict_heir_records_not_guessed():
    payload = understanding("calculation", {"الزوجة": 1, "الأم": 1, "ابن": 2})
    payload["case"]["counts"] = {"ابن": 2}
    request = SemanticRequest.model_validate(payload)
    assert request.case.counts == {"زوجة": 1, "أم": 1, "ابن": 2}
    assert request.case.parsed()["mentioned_relatives"][0] == {"relation": "زوجة", "count": 1}
