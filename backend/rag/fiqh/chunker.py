"""Arabic-aware chunking using exact contiguous source substrings."""

import hashlib
import json
import math
import re
from bisect import bisect_right

from backend.rag.fiqh.schemas import FiqhChunk, FiqhSourceRecord


def estimate_tokens(text: str) -> int:
    """Conservative estimate; Arabic words often contain several subword tokens."""
    return sum(
        max(1, math.ceil(len(word) / 3)) if re.search(r"[\u0600-\u06ff]", word) else 1
        for word in re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    )


def chunk_record(record: dict, input_file: str, target_tokens: int = 550,
                 max_tokens: int = 700, overlap_tokens: int = 80,
                 section_spans: list | None = None, min_characters: int = 100) -> list[dict]:
    if not 0 <= overlap_tokens < target_tokens <= max_tokens:
        raise ValueError("Require overlap < target <= max token budgets")
    source = FiqhSourceRecord.model_validate(record).model_dump(mode="json")
    text = source["text"]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    # Tokenize once. All chosen boundaries are between words, so prefix-count
    # differences preserve the estimator without rescanning document suffixes.
    token_ends = []
    token_totals = [0]
    for match in re.finditer(r"\w+|[^\w\s]", text, flags=re.UNICODE):
        token = match.group()
        weight = max(1, math.ceil(len(token) / 3)) if re.search(r"[\u0600-\u06ff]", token) else 1
        token_ends.append(match.end())
        token_totals.append(token_totals[-1] + weight)

    def count(start, end):
        return token_totals[bisect_right(token_ends, end)] - token_totals[bisect_right(token_ends, start)]

    def candidates_within(boundaries, start, minimum, maximum, end=None):
        candidates = []
        for index in range(bisect_right(boundaries, start), len(boundaries)):
            boundary = boundaries[index]
            if end is not None and boundary >= end:
                break
            size = count(start, boundary)
            if size > maximum:
                break
            if size >= minimum:
                candidates.append(boundary)
        return candidates
    paragraphs = [m.end() for m in re.finditer(r"(?:\r?\n[ \t]*){2,}", text)]
    sentences = [m.end() for m in re.finditer(r"[.!?؟؛]+(?:[ \t]+|\r?\n|$)", text)]
    words = [m.end() for m in re.finditer(r"\S+\s*", text)]
    chunks = []
    identity = json.dumps({k: v for k, v in source.items() if k != "text"}, ensure_ascii=False, sort_keys=True)
    start = 0
    while start < len(text):
        if count(start, len(text)) <= max_tokens:
            end = len(text)
        else:
            candidates = candidates_within(paragraphs, start, 400, max_tokens)
            if not candidates:
                candidates = candidates_within(sentences, start, 0, max_tokens)
            if not candidates:
                candidates = candidates_within(words, start, 0, max_tokens)
            if not candidates:
                raise ValueError("A source token exceeds the chunk budget; review the source manually")
            end = min(candidates, key=lambda b: abs(count(start, b) - target_tokens))
        chunk_id = hashlib.sha256(f"{identity}:{digest}:{start}:{end}".encode("utf-8")).hexdigest()
        chunk = {**source, "text": text[start:end], "chunk_id": chunk_id,
                 "document_sha256": digest, "input_file": input_file,
                 "char_start": start, "char_end": end}
        chunks.append(FiqhChunk.model_validate(chunk).model_dump(mode="json"))
        if end == len(text):
            break
        # Overlap at sentence boundaries where possible, then word boundaries.
        overlap_candidates = [b for b in candidates_within(sentences, start, 0, max_tokens, end)
                              if 60 <= count(b, end) <= 100]
        if not overlap_candidates:
            overlap_candidates = [b for b in candidates_within(words, start, 0, max_tokens, end)
                                  if count(b, end) <= overlap_tokens]
        start = min(overlap_candidates, key=lambda b: abs(count(b, end) - overlap_tokens)) if overlap_tokens and overlap_candidates else end
    # Merge tiny spans as contiguous source slices, retaining all characters.
    spans = []
    pending_start = None
    for chunk in chunks:
        begin = pending_start if pending_start is not None else chunk["char_start"]
        finish = chunk["char_end"]
        pending_start = None
        if finish - begin < min_characters:
            if spans:
                spans[-1][1] = max(spans[-1][1], finish)
            else:
                pending_start = begin
        else:
            spans.append([begin, finish])
    if pending_start is not None:
        spans.append([pending_start, len(text)])  # Short standalone documents retain text.
    rebuilt = []
    for begin, finish in spans:
        metadata = {k: v for k, v in source.items() if k != "text"}
        for offset, heading in section_spans or []:
            if offset > begin:
                break
            metadata["section"] = heading
        identity = json.dumps(metadata, ensure_ascii=False, sort_keys=True)
        chunk_id = hashlib.sha256(f"{identity}:{digest}:{begin}:{finish}".encode("utf-8")).hexdigest()
        rebuilt.append(FiqhChunk.model_validate({**metadata, "text": text[begin:finish],
            "chunk_id": chunk_id, "document_sha256": digest, "input_file": input_file,
            "char_start": begin, "char_end": finish}).model_dump(mode="json"))
    return rebuilt
