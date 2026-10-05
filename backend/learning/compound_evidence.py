"""Educational views of confirmed existing rules, never executable new rules."""
import hashlib
import json
from backend.rag.source_validation import validate_rule_records

_ALLOWED = {"wife_with_descendant", "mother_with_child", "sons_and_daughters"}


def educational_rule_summaries(confirmed_rules: list[dict]) -> list[dict]:
    """Caller supplies rules already selected for the example's structured facts.

    These repository summaries are not original Quran passages and are never
    returned as immutable source quotations. Conditions stay attached.
    """
    validated = validate_rule_records(confirmed_rules)
    return [{"rule_id": rule["rule_id"], "text": rule["rule"],
             "content_kind": "structured_rule_summary", "immutable_text": False,
             "conditions": rule["conditions"], "applies_to": rule["applies_to"],
             "source": dict(rule["source"]),
             "provenance": {"repository_file": "data/sources/inheritance_rules.json",
                 "rule_id": rule["rule_id"], "source": dict(rule["source"]),
                 "text_sha256": hashlib.sha256(rule["rule"].encode()).hexdigest(),
                 "rule_sha256": hashlib.sha256(json.dumps(rule, ensure_ascii=False,
                     sort_keys=True, separators=(",", ":")).encode()).hexdigest()}}
            for rule in validated if rule["rule_id"] in _ALLOWED]
