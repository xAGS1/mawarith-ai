"""Arabic-aware chunking using exact contiguous source substrings."""

import hashlib
import json
import math
import re

from backend.rag.fiqh.schemas import FiqhChunk, FiqhSourceRecord


def estimate_tokens(text: str) -> int:
    """Conservative estimate; Arabic words often contain several subword tokens."""
    return sum(
        max(1, math.ceil(len(word) / 3)) if re.search(r"[\u0600-\u06ff]", word) else 1
        for word in re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    )


def chunk_record(record: dict, input_file: str, target_tokens: int = 550,
                 max_tokens: int = 700, overlap_tokens: int = 80) -> list[dict]:
    if not 0 <= overlap_tokens < target_tokens <= max_tokens:
        raise ValueError("Require overlap < target <= max token budgets")
    source = FiqhSourceRecord.model_validate(record).model_dump(mode="json")
    text = source["text"]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    paragraphs = [m.end() for m in re.finditer(r"(?:\r?\n[ \t]*){2,}", text)]
    sentences = [m.end() for m in re.finditer(r"[.!?؟؛]+(?:[ \t]+|\r?\n|$)", text)]
    words = [m.end() for m in re.finditer(r"\S+\s*", text)]
    chunks = []
    start = 0
    while start < len(text):
        if estimate_tokens(text[start:]) <= max_tokens:
            end = len(text)
        else:
            candidates = [b for b in paragraphs if b > start and 400 <= estimate_tokens(text[start:b]) <= max_tokens]
            if not candidates:
                candidates = [b for b in sentences if b > start and estimate_tokens(text[start:b]) <= max_tokens]
            if not candidates:
                candidates = [b for b in words if b > start and estimate_tokens(text[start:b]) <= max_tokens]
            if not candidates:
                raise ValueError("A source token exceeds the chunk budget; review the source manually")
            end = min(candidates, key=lambda b: abs(estimate_tokens(text[start:b]) - target_tokens))
        identity = json.dumps({k: v for k, v in source.items() if k != "text"}, ensure_ascii=False, sort_keys=True)
        chunk_id = hashlib.sha256(f"{identity}:{digest}:{start}:{end}".encode("utf-8")).hexdigest()
        chunk = {**source, "text": text[start:end], "chunk_id": chunk_id,
                 "document_sha256": digest, "input_file": input_file,
                 "char_start": start, "char_end": end}
        chunks.append(FiqhChunk.model_validate(chunk).model_dump(mode="json"))
        if end == len(text):
            break
        # Overlap at sentence boundaries where possible, then word boundaries.
        overlap_candidates = [b for b in sentences if start < b < end and 60 <= estimate_tokens(text[b:end]) <= 100]
        if not overlap_candidates:
            overlap_candidates = [b for b in words if start < b < end and estimate_tokens(text[b:end]) <= overlap_tokens]
        start = min(overlap_candidates, key=lambda b: abs(estimate_tokens(text[b:end]) - overlap_tokens)) if overlap_tokens and overlap_candidates else end
    return chunks
