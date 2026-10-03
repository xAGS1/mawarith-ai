"""Fetch exact Arabic text from QuranEnc, never from a language model."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

import requests


CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "sources" / "quran_cache"
API_BASE = "https://quranenc.com/api/v1/translation/aya/english_saheeh"


class QuranSourceError(RuntimeError):
    """The provider did not return a valid verse for the requested reference."""


def validate_verse_numbers(surah: int, ayah: int) -> None:
    if type(surah) is not int or not 1 <= surah <= 114 or type(ayah) is not int or not 1 <= ayah <= 286:
        raise ValueError("Invalid Quran surah or ayah number")


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _valid_cache(record, surah, ayah):
    return (
        isinstance(record, dict)
        and record.get("provider") == "quranenc"
        and record.get("source_type") == "quran"
        and record.get("reference") == f"{surah}:{ayah}"
        and record.get("surah") == surah and record.get("ayah") == ayah
        and record.get("immutable_text") is True
        and record.get("retrieval_status") == "available"
        and isinstance(record.get("arabic_text"), str)
        and bool(record["arabic_text"].strip())
        and record.get("text_sha256") == _checksum(record["arabic_text"])
    )


def get_quran_verse(surah: int, ayah: int) -> dict:
    """Return the provider's exact text; validate identity and cache atomically.

    A checksum detects accidental cache corruption, not malicious modification.
    The translation endpoint's translation and footnotes are never used as text.
    """
    validate_verse_numbers(surah, ayah)
    cache_path = CACHE_DIR / f"{surah}_{ayah}.json"
    try:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if _valid_cache(cached, surah, ayah):
            return cached
    except (OSError, ValueError):
        pass

    url = f"{API_BASE}/{surah}/{ayah}"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    try:
        payload = response.json()["result"]
        if int(payload["sura"]) != surah or int(payload["aya"]) != ayah:
            raise QuranSourceError("QuranEnc returned a different verse")
        text = payload["arabic_text"]
        if not isinstance(text, str) or not text.strip():
            raise QuranSourceError("QuranEnc did not return Arabic verse text")
    except (ValueError, KeyError, TypeError) as exc:
        raise QuranSourceError("Invalid QuranEnc verse response") from exc

    verse = {
        "source_type": "quran", "provider": "quranenc",
        "surah": surah, "ayah": ayah, "reference": f"{surah}:{ayah}",
        "arabic_text": text, "immutable_text": True,
        "retrieval_status": "available", "source_url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "text_sha256": _checksum(text),
    }
    temporary_path = None
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=CACHE_DIR, suffix=".tmp", delete=False) as cached_file:
            temporary_path = Path(cached_file.name)
            json.dump(verse, cached_file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, cache_path)
    except OSError:
        # A cache write failure must not discard a successful trusted retrieval.
        verse["cache_status"] = "write_failed"
    finally:
        if temporary_path is not None and temporary_path.exists():
            try:
                temporary_path.unlink()
            except OSError:
                pass
    return verse
