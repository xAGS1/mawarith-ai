"""Neutral fixtures verify catalogs; no religious quotations or calculations."""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.app import app, ask_endpoint, EducationalRequest
from backend.learning import catalogs, router
from backend.rules import educational_concepts


def test_catalog_ids_and_references():
    cards = catalogs.list_concepts()
    ids = {card["concept_id"] for card in cards}
    assert len(ids) == len(cards) == 7
    for card in cards:
        assert set(card["related_concepts"]) <= ids
        assert card["title_ar"] and card["title_en"]
        assert set(card["learn_question"]) == {"ar", "en"}
        assert card["availability"] == "limited"
        assert card["short_definition"] is None
    examples = catalogs.list_examples()
    assert 3 <= len(examples) <= 5
    assert len({e["example_id"] for e in examples}) == len(examples)
    for example in examples:
        assert set(example["concepts"]) <= ids
        assert example["case_supported"] is True
        assert "result" not in example and "shares" not in example


def test_cards_use_source_bound_metadata_only(monkeypatch):
    monkeypatch.setattr(catalogs, "load_chunks", lambda: [{"chunk_id": "neutral", "text": "Neutral fixture text.",
        "source_name": "Fixture", "verified_source": True, "volume": 3}])
    monkeypatch.setattr(educational_concepts, "CONCEPTS", (
        {"concept_id": "fixed_share", "queries": ("الفرض",), "anchors": ("Neutral fixture",),
         "ar": {"term": "مصطلح تجريبي", "explanation": "تعريف تجريبي محايد."},
         "en": {"term": "Test term", "explanation": "Neutral test definition."}},
        {"concept_id": "residuary", "queries": ("العصبة", "التعصيب"), "anchors": ("Neutral fixture",),
         "ar": {"term": "مصطلح تجريبي", "explanation": "تعريف تجريبي محايد."},
         "en": {"term": "Test term", "explanation": "Neutral test definition."}},
    ))
    cards = catalogs.list_concepts()
    available = {c["concept_id"] for c in cards if c["availability"] == "available"}
    assert available == {"fixed_share", "residuary_heirs", "residuary_inheritance"}
    for card in cards:
        if card["availability"] == "available":
            assert card["short_definition"]["en"] == "Neutral test definition."
            assert card["sources"][0]["chunk_id"] == "neutral"
            assert "text" not in card["sources"][0]
        else:
            assert card["short_definition"] is None
    assert all(c["availability"] == "limited" for c in cards if c["concept_id"] in {"blocking", "awl", "radd", "fixed_share_heirs"})


def test_invalid_corpus_does_not_guess_definitions(monkeypatch):
    monkeypatch.setattr(catalogs, "load_chunks", Mock(side_effect=ValueError("Invalid corpus")))
    assert all(c["short_definition"] is None for c in catalogs.list_concepts())


def test_beginner_path_has_valid_steps():
    path = catalogs.list_paths()[0]
    ids = {c["concept_id"] for c in catalogs.list_concepts()}
    examples = {e["example_id"]: e for e in catalogs.list_examples()}
    assert path["path_id"] == "inheritance_beginner"
    assert len(path["steps"]) == 7
    assert len({s["step_id"] for s in path["steps"]}) == 7
    for step in path["steps"]:
        assert set(step["concepts"]) <= ids
        assert set(step["question"]) == {"ar", "en"}
        assert step["mode"] in {"learn", "case"}
        if "example_id" in step:
            assert step["question"]["ar"] == examples[step["example_id"]]["scenario_ar"]
    assert "progress" not in path


def test_example_support_is_checked_not_assumed(monkeypatch):
    monkeypatch.setattr(catalogs, "retrieve_rules", lambda *args: [])
    assert all(e["case_supported"] is False for e in catalogs.list_examples())


def test_returns_do_not_mutate_catalog():
    examples = catalogs.list_examples()
    examples[0]["concepts"].clear()
    assert catalogs.list_examples()[0]["concepts"]
    paths = catalogs.list_paths()
    paths[0]["steps"].clear()
    assert len(catalogs.list_paths()[0]["steps"]) == 7


@pytest.mark.parametrize("listing,detail,key", [
    (router.concepts, router.concept, "concept_id"),
    (router.paths, router.path, "path_id"),
    (router.examples, router.example, "example_id"),
])
def test_resource_detail_and_missing(listing, detail, key):
    first = listing()[0]
    assert detail(first[key]) == first
    with pytest.raises(HTTPException) as error:
        detail("missing")
    assert error.value.status_code == 404


def test_api_routes_and_ask_contract_unchanged(monkeypatch):
    routes = app.openapi()["paths"]
    for path in ("/learn/concepts", "/learn/concepts/{concept_id}",
                 "/learn/paths", "/learn/paths/{path_id}",
                 "/learn/examples", "/learn/examples/{example_id}"):
        assert set(routes[path]) == {"get"}
    assert "post" in routes["/ask"] and "post" in routes["/analyze-case"]
    assert EducationalRequest(question="Test").mode == "learn"
    import backend.app as api
    expected = {"mode": "case", "result": "existing pipeline response"}
    run = Mock(return_value=expected)
    monkeypatch.setattr(api, "run_request", run)
    assert ask_endpoint(EducationalRequest(question="Test", mode="case")) == expected
    run.assert_called_once_with("Test", "case")
