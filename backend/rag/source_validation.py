"""Validate the current Quran-only source batch before retrieval."""

from fractions import Fraction


ALLOWED_REFERENCES = frozenset({"4:11", "4:12", "4:176"})
REQUIRED_FIELDS = frozenset({"rule_id", "applies_to", "conditions", "result", "topic", "rule", "source"})


def validate_rule_records(records: list) -> list:
    """Raise ValueError for invalid records; retain complete original metadata."""
    if not isinstance(records, list):
        raise ValueError("Source library must be a list")
    identifiers = set()
    for index, record in enumerate(records):
        def invalid(message):
            raise ValueError(f"Source record {index}: {message}")

        if not isinstance(record, dict) or not REQUIRED_FIELDS.issubset(record):
            invalid("missing required rule fields")
        for field in ("rule_id", "topic", "rule"):
            if not isinstance(record[field], str) or not record[field].strip():
                invalid(f"{field} must be a nonempty string")
        if record["rule_id"] in identifiers:
            invalid("duplicate rule_id")
        identifiers.add(record["rule_id"])
        targets = record["applies_to"]
        if not isinstance(targets, list) or not targets or any(not isinstance(r, str) or not r.strip() for r in targets):
            invalid("applies_to must contain relation names")
        conditions = record["conditions"]
        if not isinstance(conditions, dict):
            invalid("conditions must be an object")
        for feature, expected in conditions.items():
            if not isinstance(feature, str) or not feature:
                invalid("condition keys must be feature names")
            if feature.endswith(("_gte", "_lte")):
                if type(expected) is not int:
                    invalid("threshold conditions require integers")
            elif isinstance(expected, dict):
                if not expected or not set(expected).issubset({"eq", "min", "max"}) or any(type(v) is not int for v in expected.values()):
                    invalid("invalid integer comparison condition")
            elif type(expected) not in (bool, int):
                invalid("equality conditions require booleans or integers")
        result = record["result"]
        if not isinstance(result, dict) or not result:
            invalid("result must be a nonempty object")
        if "fraction" in result:
            try:
                fraction = Fraction(result["fraction"])
            except (ValueError, TypeError, ZeroDivisionError):
                invalid("invalid fraction")
            if not isinstance(result["fraction"], str) or not 0 < fraction <= 1:
                invalid("fraction must be a string between zero and one")
        elif result.get("allocation") == "residue":
            if any(type(result.get(k)) is not int or result[k] <= 0 for k in ("male_weight", "female_weight")):
                invalid("residue allocation requires positive integer weights")
        else:
            invalid("unsupported result")
        source = record["source"]
        if not isinstance(source, dict) or any(not isinstance(source.get(k), str) or not source[k].strip() for k in ("source_type", "source_name", "reference")):
            invalid("missing source metadata")
        if source["source_type"] != "quran" or source["reference"] not in ALLOWED_REFERENCES:
            invalid("source must reference Quran 4:11, 4:12 or 4:176")
    return records
