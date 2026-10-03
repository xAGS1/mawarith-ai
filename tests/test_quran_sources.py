import copy
import json
from unittest.mock import Mock, patch

import pytest
import requests

from backend.pipeline.qwen_pipeline import run_pipeline
from backend.sources.quran import quranenc
from backend.sources.router import enrich_sources, parse_quran_reference


# Synthetic provider fixtures test exact preservation, not Quran authenticity.
TEXT = "  نص اختبار المصدر\u00a0\n"


def rule(reference="4:12"):
    return {"rule_id": "wife_without_descendant", "topic": "زوجة", "rule": "1/4",
            "applies_to": ["زوجة"], "conditions": {"has_descendant": False},
            "result": {"fraction": "1/4"},
            "source": {"source_type": "quran", "source_name": "القرآن الكريم", "reference": reference}}


def response(surah=4, ayah=12, text=TEXT):
    result = Mock()
    result.json.return_value = {"result": {"sura": str(surah), "aya": str(ayah), "arabic_text": text,
                                           "translation": "NEVER USE TRANSLATION"}}
    return result


@pytest.fixture(autouse=True)
def isolated_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(quranenc, "CACHE_DIR", tmp_path / "cache")
    get = Mock(side_effect=requests.ConnectionError("offline test"))
    monkeypatch.setattr(quranenc.requests, "get", get)
    return get


def test_reference_parsing():
    assert parse_quran_reference("4:12") == (4, 12)


@pytest.mark.parametrize("reference", ["../4:12", "4/12", "0:12", "115:1", "4:0", "4:999", None])
def test_invalid_references(reference):
    with pytest.raises(ValueError):
        parse_quran_reference(reference)


def test_adapter_preserves_exact_text_and_cache_avoids_network(isolated_sources):
    isolated_sources.side_effect = None
    isolated_sources.return_value = response()
    verse = quranenc.get_quran_verse(4, 12)
    assert verse["arabic_text"] == TEXT
    assert verse["immutable_text"] is True
    assert verse["provider"] == "quranenc"
    assert verse["reference"] == "4:12"
    assert verse["fetched_at"]
    assert "translation" not in verse
    assert json.loads((quranenc.CACHE_DIR / "4_12.json").read_text(encoding="utf-8")) == verse
    isolated_sources.reset_mock()
    isolated_sources.side_effect = requests.ConnectionError("offline")
    assert quranenc.get_quran_verse(4, 12) == verse
    isolated_sources.assert_not_called()


def test_router_enriches_without_mutating_rules_and_deduplicates(isolated_sources):
    isolated_sources.side_effect = None
    isolated_sources.return_value = response()
    rules = [rule(), rule()]
    original = copy.deepcopy(rules)
    enriched = enrich_sources(rules)
    assert rules == original
    assert enriched[0]["source"]["arabic_text"] == TEXT
    assert enriched[0]["source"]["source_name"] == "القرآن الكريم"
    assert enriched[0]["rule"] == original[0]["rule"]
    assert enriched[0]["source"]["retrieval_status"] == "available"
    assert isolated_sources.call_count == 1


def test_network_failure_preserves_reference_without_invented_text(isolated_sources):
    rules = [rule(), rule()]
    enriched = enrich_sources(rules)
    assert enriched[0]["rule"] == rules[0]["rule"]
    source = enriched[0]["source"]
    assert source["reference"] == "4:12"
    assert source["retrieval_status"] == "unavailable"
    assert source.get("arabic_text") is None
    assert source.get("immutable_text") is None
    assert isolated_sources.call_count == 1


@pytest.mark.parametrize("bad", [response(ayah=11), response(text=""), response(text=None)])
def test_invalid_provider_payload_never_becomes_trusted_text(isolated_sources, bad):
    isolated_sources.side_effect = None
    isolated_sources.return_value = bad
    source = enrich_sources([rule()])[0]["source"]
    assert source["retrieval_status"] == "unavailable"
    assert "arabic_text" not in source


def test_translation_only_payload_is_not_a_verse(isolated_sources):
    isolated_sources.side_effect = None
    isolated_sources.return_value = response()
    del isolated_sources.return_value.json.return_value["result"]["arabic_text"]
    assert enrich_sources([rule()])[0]["source"]["retrieval_status"] == "unavailable"


def test_corrupt_cache_is_refetched(isolated_sources):
    isolated_sources.side_effect = None
    isolated_sources.return_value = response()
    verse = quranenc.get_quran_verse(4, 12)
    cache = quranenc.CACHE_DIR / "4_12.json"
    verse["arabic_text"] = "modified"
    cache.write_text(json.dumps(verse), encoding="utf-8")
    assert quranenc.get_quran_verse(4, 12)["arabic_text"] == TEXT
    assert isolated_sources.call_count == 2


def test_pipeline_keeps_source_text_out_of_reasoning_input(isolated_sources):
    isolated_sources.side_effect = None
    isolated_sources.return_value = response()
    parsed = {"mentioned_relatives": [{"relation": "زوجة", "count": 1}]}
    generated = {"heirs": [{"heir": "زوجة", "count": 1}], "blocked": [], "shares": [],
                 "awl_or_radd": "لا", "post_tasil": {"distribution": [
                     {"heir": "زوجة", "count": 1, "per_head_shares": "1/4"}]}}
    with (
        patch("backend.pipeline.qwen_pipeline.parse_relations", return_value=parsed),
        patch("backend.pipeline.qwen_pipeline.analyze_case", return_value=generated) as reasoner,
    ):
        output = run_pipeline("سؤال اختبار")
    assert output["sources"][0]["source"]["arabic_text"] == TEXT
    assert output["sources"][0]["rule_id"] == "wife_without_descendant"
    assert "arabic_text" not in reasoner.call_args.kwargs["sources"][0]["source"]
    assert TEXT not in json.dumps(output["result"], ensure_ascii=False)
    assert output["result"]["shares"][0]["fraction"] == "1/4"
    assert output["decision_state"] == "ready"


def test_unavailable_source_still_separates_reference_from_result():
    source = enrich_sources([rule()])[0]["source"]
    assert source["retrieval_status"] == "unavailable"
    assert source["reference"] == "4:12"
