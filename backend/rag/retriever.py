"""Retrieve local rules by exact relation names, preserving source metadata."""

import json
from pathlib import Path


RULES_PATH = Path(__file__).resolve().parents[2] / "data" / "sources" / "inheritance_rules.json"


def retrieve_rules(parsed_relations: dict) -> list:
    """Return candidate rules; their stated conditions still govern application.

    Match whole relation names so, for example, بنت ابن does not match بنت.
    Resolve the source file relative to the project, independent of the cwd.
    """
    relations = {
        item["relation"].strip()
        for item in parsed_relations.get("mentioned_relatives", [])
        if item["count"] > 0
    }
    with RULES_PATH.open(encoding="utf-8") as source_file:
        rules = json.load(source_file)

    return [rule for rule in rules if relations.intersection(rule["relations"])]
