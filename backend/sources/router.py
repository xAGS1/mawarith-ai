"""Enrich rule sources independently of parsing, reasoning and verification."""

from copy import deepcopy
import re

import requests

from backend.sources.quran.quranenc import QuranSourceError, get_quran_verse, validate_verse_numbers


def parse_quran_reference(reference: str) -> tuple[int, int]:
    if not isinstance(reference, str) or not re.fullmatch(r"[0-9]{1,3}:[0-9]{1,3}", reference):
        raise ValueError("Quran reference must have the form surah:ayah")
    surah, ayah = map(int, reference.split(":"))
    validate_verse_numbers(surah, ayah)
    return surah, ayah


def enrich_sources(retrieved_rules: list) -> list:
    """Preserve rule records; attach only adapter-returned Quran text.

    Deduplicate provider calls per reference, including failed requests.
    Failure keeps the reference and rule but adds no text or immutability claim.
    """
    enriched = deepcopy(retrieved_rules)
    resolved = {}
    for rule in enriched:
        source = rule.get("source", {})
        if source.get("source_type") != "quran":
            continue
        reference = source.get("reference")
        # Supplied text is not trusted merely because it is present in a rule.
        for field in ("arabic_text", "immutable_text", "text_sha256"):
            source.pop(field, None)
        try:
            numbers = parse_quran_reference(reference)
            if numbers not in resolved:
                try:
                    resolved[numbers] = get_quran_verse(*numbers)
                except (requests.RequestException, QuranSourceError, ValueError, OSError):
                    resolved[numbers] = {"provider": "quranenc", "retrieval_status": "unavailable"}
            source.update(deepcopy(resolved[numbers]))
        except ValueError:
            source.update(provider="quranenc", retrieval_status="unavailable")
    return enriched
