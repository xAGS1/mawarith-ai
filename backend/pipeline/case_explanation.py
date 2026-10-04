"""AI chooses relevant verified claims; Python renders their factual wording."""
import re
import requests
from backend.llm import qwen_understanding


def explain_case_question(question: str, understanding, plan: list[dict]) -> tuple[str, list[dict], str]:
    claims = [c for c in plan if c["support"] == "structured" and c["statement"]]
    # For the common son/daughter comparison, only their shared rule answers why.
    if re.search(r"ابن|بنت|son|daughter", question, re.I):
        claims = [c for c in claims if {"ابن", "بنت"} <= set(c.get("applies_to", []))]
    if not claims:
        return "", [], "no_supported_claim"
    origin = "ai_selection"
    try:
        selected = qwen_understanding.select_claims(question, understanding.language, understanding.depth,
            [{k: c[k] for k in ("claim_id", "concept_or_rule_id", "statement", "source_id")} for c in claims])
        ids = selected["claim_ids"]
        known = {c["claim_id"]: c for c in claims}
        if (set(selected) != {"claim_ids"} or not isinstance(ids, list) or not ids
                or any(not isinstance(id, str) or id not in known for id in ids)):
            raise ValueError("Unsupported claim selection")
        claims = [known[id] for id in dict.fromkeys(ids)]
    except (requests.RequestException, ValueError, KeyError, TypeError):
        origin = "deterministic_fallback"
    if understanding.depth == "simple":
        claims = claims[:1]
    lead = "القاعدة الموثقة ذات الصلة بسؤالك:" if understanding.language == "ar" else "The documented rule relevant to your question (original Arabic wording):"
    # No model-authored factual prose can change a fraction, heir or condition.
    return lead + "\n" + "\n".join(c["statement"] for c in claims), claims, origin
