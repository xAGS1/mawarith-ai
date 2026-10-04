import pytest
from backend.learning.knowledge import ContentItem, Definition, StructuredConcept, verified_item, verified_properties
from backend.learning.comparisons import compare_concepts


def concept(id, text):
    source = {"verified_source": True, "exact_text": text, "source_name": "Neutral fixture",
              "source_url": "https://example.invalid"}
    item = {"value": text, "status": "source_verbatim", "source_id": id, "reviewer": None, "reviewed_at": None}
    return {"id": id, "title_ar": id, "title_en": id, "verified": True,
            "definition": {"text": text, **{k: v for k, v in item.items() if k != "value"}},
            "source_records": {id: source}, "properties": {"neutral_property": item}}


@pytest.mark.parametrize("status", ["source_verbatim", "reviewed_summary"])
def test_verified_items_require_source_ids(status):
    with pytest.raises(ValueError):
        ContentItem(value="Neutral", status=status)
    with pytest.raises(ValueError):
        Definition(text="Neutral", status=status)


@pytest.mark.parametrize("missing", ["reviewer", "reviewed_at"])
def test_reviewed_summary_requires_review_metadata(missing):
    item = {"value": "Neutral summary", "status": "reviewed_summary", "source_id": "fixture",
            "reviewer": "Synthetic fixture reviewer", "reviewed_at": "2026-01-01"}
    item[missing] = None
    with pytest.raises(ValueError):
        ContentItem.model_validate(item)


def test_exact_passage_validation_preserves_whitespace():
    source = {"fixture": {"verified_source": True, "exact_text": "Neutral text.\n  Spaces preserved."}}
    item = {"value": "\n  Spaces preserved.", "status": "source_verbatim", "source_id": "fixture"}
    assert verified_item(item, source)
    assert not verified_item({**item, "value": "Spaces  rewritten."}, source)
    assert not verified_item({**item, "source_id": "unknown"}, source)
    assert not verified_item(item, {"fixture": {"verified_source": False, "exact_text": source["fixture"]["exact_text"]}})
    assert not verified_item({**item, "value": True}, source)


def test_schema_rejects_untraceable_verbatim():
    entry = concept("neutral", "Neutral text.")
    payload = {k: entry[k] for k in ("id", "title_ar", "title_en", "definition", "properties", "source_records")}
    assert StructuredConcept.model_validate(payload).definition.status == "source_verbatim"
    payload["properties"]["neutral_property"]["value"] = "Not present."
    with pytest.raises(ValueError):
        StructuredConcept.model_validate(payload)


def test_draft_and_unsupported_properties_are_never_rendered():
    a, b = concept("a", "Neutral A."), concept("b", "Neutral B.")
    for entry in (a, b):
        entry["properties"]["draft"] = {"value": "Hidden draft", "status": "draft"}
        entry["properties"]["unsupported"] = {"value": "Invented text", "status": "source_verbatim", "source_id": entry["id"]}
    assert set(verified_properties(a)) == {"neutral_property"}
    result = compare_concepts([a, b], "en")
    assert "Hidden draft" not in result["answer"]
    assert "Invented text" not in result["answer"]
    a["definition"]["status"] = "draft"
    assert compare_concepts([a, b], "en") is None


def test_no_shared_safe_properties_falls_back():
    a, b = concept("a", "Neutral A."), concept("b", "Neutral B.")
    b["properties"]["different"] = b["properties"].pop("neutral_property")
    assert compare_concepts([a, b], "en") is None


def test_generic_comparison_preserves_each_property_source_mapping():
    a, b = concept("a", "Neutral A."), concept("b", "Neutral B.")
    for entry in (a, b):
        extra_id = entry["id"] + "_extra"
        entry["source_records"][extra_id] = {"verified_source": True, "exact_text": "Neutral extra.", "source_name": "Other fixture"}
        entry["properties"]["extra"] = {"value": "Neutral extra.", "status": "source_verbatim",
            "source_id": extra_id, "reviewer": None, "reviewed_at": None}
    result = compare_concepts([a, b], "en")
    assert len(result["sources"]) == 4
    for record in result["sources"]:
        original = a if record["concept_id"] == "a" else b
        for link in record["property_links"]:
            assert original["properties"][link["property"]]["source_id"] == record["source_id"] == link["source_id"]


def test_reviewed_summary_never_enters_exact_source_excerpts():
    a, b = concept("a", "Neutral A."), concept("b", "Neutral B.")
    for entry in (a, b):
        entry["properties"]["neutral_property"].update(value="Reviewed neutral summary.",
            status="reviewed_summary", reviewer="Synthetic fixture reviewer", reviewed_at="2026-01-01")
    result = compare_concepts([a, b], "en")
    assert "Reviewed educational summary" in result["answer"]
    assert all("Reviewed neutral summary" not in excerpt["text"] for excerpt in result["source_excerpts"])


def test_migration_uses_existing_evidence_without_review_invention(monkeypatch):
    from backend.learning import concept_catalog as catalog
    from backend.rules.educational_concepts import CONCEPTS
    # Reuse the repository's existing anchors; no new religious content is authored.
    for id, metadata in (("fixed_share", CONCEPTS[1]), ("residuary_heirs", CONCEPTS[0])):
        source = {"chunk_id": id, "source_name": "Synthetic fixture", "source_url": "https://example.invalid", "verified_source": True}
        passage = " ".join(metadata["anchors"])
        record = {"id": id, "verified": False, "properties": {}}
        catalog._migrate_content(record, {"ar": metadata["ar"]["explanation"], "en": metadata["en"]["explanation"]}, passage, source)
        assert record["verified"]
        assert all(item["status"] == "draft" and item["reviewer"] is None for item in record["educational_summaries"].values())
        assert all(verified_item(item, record["source_records"]) for item in record["properties"].values())
        if id == "residuary_heirs":
            assert all(item["value"] == passage for item in record["properties"].values())
