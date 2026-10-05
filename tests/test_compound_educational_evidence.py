import hashlib
import json
from pathlib import Path
from backend.learning import catalogs
from backend.learning.compound_evidence import educational_rule_summaries


def test_compound_summaries_preserve_existing_conditions_references_and_hashes():
    rules = json.loads((Path(__file__).resolve().parents[1] / "data/sources/inheritance_rules.json").read_text(encoding="utf-8"))
    evidence = educational_rule_summaries(rules)
    assert {e["rule_id"] for e in evidence} == {"wife_with_descendant", "mother_with_child", "sons_and_daughters"}
    for entry in evidence:
        original = next(r for r in rules if r["rule_id"] == entry["rule_id"])
        assert entry["text"] == original["rule"]
        assert entry["source"] == original["source"]
        assert entry["conditions"] == original["conditions"]
        assert entry["content_kind"] == "structured_rule_summary"
        assert entry["immutable_text"] is False
        assert entry["provenance"]["text_sha256"] == hashlib.sha256(original["rule"].encode()).hexdigest()
        assert entry["provenance"]["rule_sha256"] == hashlib.sha256(json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_existing_examples_expose_only_their_confirmed_educational_rules():
    examples = {e["example_id"]: e for e in catalogs.list_examples()}
    assert {e["rule_id"] for e in examples["wife_mother_children"]["educational_evidence"]} == {
        "wife_with_descendant", "mother_with_child", "sons_and_daughters"}
    assert {e["rule_id"] for e in examples["wife_son_daughter"]["educational_evidence"]} == {
        "wife_with_descendant", "sons_and_daughters"}
    assert {e["rule_id"] for e in examples["mother_son_daughters"]["educational_evidence"]} == {
        "mother_with_child", "sons_and_daughters"}


def test_unsupported_examples_do_not_expose_rule_summaries(monkeypatch):
    monkeypatch.setattr(catalogs, "retrieve_rules", lambda *args: [])
    assert all(not e["educational_evidence"] for e in catalogs.list_examples())
