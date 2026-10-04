from unittest.mock import Mock

import pytest

from backend.learning import comparisons
from backend.pipeline import learn_pipeline as learn
from backend.rules.educational_concepts import CONCEPTS


@pytest.fixture
def verified_pair(monkeypatch):
    records = {}
    for id, metadata in (("fixed_share", CONCEPTS[1]), ("residuary_heirs", CONCEPTS[0])):
        # Neutral synthetic evidence; factual definitions reuse repository metadata.
        records[id] = {
            "id": id, "verified": True,
            "definition_ar": metadata["ar"]["explanation"],
            "definition_en": metadata["en"]["explanation"],
            "exact_excerpt": f"Neutral fixture evidence for {id}.",
            "source_title": "Neutral test source", "source_entry": id,
            "reference": id,
            "source": {"chunk_id": id, "source_name": "Neutral test source",
                       "source_url": "https://example.invalid", "verified_source": True},
        }
    monkeypatch.setattr(comparisons, "get_curated_concept", records.get)
    return records


@pytest.mark.parametrize("question,language", [
    ("ما الفرق بين الفرض والتعصيب؟", "ar"),
    ("What is the difference between fixed shares and residuary inheritance?", "en"),
])
def test_verified_comparison_preserves_definitions_and_separate_evidence(monkeypatch, verified_pair, question, language):
    rag, model = Mock(side_effect=AssertionError("RAG must not run")), Mock(side_effect=AssertionError("LLM must not run"))
    monkeypatch.setattr(learn, "retrieve_educational_evidence", rag)
    monkeypatch.setattr(learn.provider, "explain", model)
    result = learn.run_learn(question)
    assert result["decision_state"] == "ready"
    assert result["evidence_status"] == "supported"
    assert result["answer"] == "\n\n".join(
        verified_pair[id][f"definition_{language}"] + f" [E{i}]"
        for i, id in enumerate(("fixed_share", "residuary_heirs"), 1))
    for i, id in enumerate(("fixed_share", "residuary_heirs"), 1):
        excerpt = result["source_excerpts"][i - 1]
        assert excerpt["text"] == verified_pair[id]["exact_excerpt"]
        assert excerpt["concept_id"] == id
        assert excerpt["evidence_id"] == f"E{i}"
        assert result["sources"][i - 1]["chunk_id"] == id
    rag.assert_not_called()
    model.assert_not_called()
    # Equality above disallows every added/recombined condition, including this bug.
    assert "الباقي إذا لم يوجد صاحب فرض" not in result["answer"]
    assert "remainder if there is no fixed-share heir" not in result["answer"]


def test_one_unverified_concept_uses_existing_safe_fallback(monkeypatch, verified_pair):
    verified_pair["residuary_heirs"]["verified"] = False
    rag = Mock(return_value=[])
    monkeypatch.setattr(learn, "retrieve_educational_evidence", rag)
    result = learn.run_learn("ما الفرق بين الفرض والتعصيب؟")
    rag.assert_called_once()
    assert result["evidence_status"] == "insufficient"
    assert result["source_excerpts"] == []
    assert result["sources"] == []


@pytest.mark.parametrize("question", [
    "ما الفرق بين الفرض والتعصيب مع وجود البنات؟",
    "What is the difference between fixed shares and residuary inheritance with daughters?",
    "ما الفرق بين أصحاب الفروض النسبية والتعصيب؟",
    "مات وترك بنتا وأخا", "What is a fixed share?",
])
def test_comparison_matching_does_not_broaden(verified_pair, question):
    assert comparisons.curated_comparison(question, "ar") is None


def test_reverse_comparison_keeps_evidence_order(verified_pair):
    result = comparisons.curated_comparison("ما الفرق بين التعصيب والفرض؟", "ar")
    assert result["sources"][0]["concept_id"] == "residuary_heirs"
    assert result["sources"][1]["concept_id"] == "fixed_share"
    assert result["answer"].split("\n\n")[0] == verified_pair["residuary_heirs"]["definition_ar"] + " [E1]"


def test_case_dispatch_never_calls_educational_comparison(monkeypatch):
    from backend.pipeline import educational_pipeline as shared
    comparison = Mock(side_effect=AssertionError("Case mode must not compare concepts"))
    monkeypatch.setattr(learn, "curated_comparison", comparison)
    case = {"decision_state": "ready", "result": {"verification": {"is_consistent": True}},
            "sources": [], "fiqh_evidence": []}
    solver = Mock(return_value=case)
    monkeypatch.setattr(shared, "run_pipeline", solver)
    result = shared.run_request("A person died leaving heirs.", "case")
    assert result["decision_state"] == "ready"
    assert result["case_details"] == case
    solver.assert_called_once()
    comparison.assert_not_called()
