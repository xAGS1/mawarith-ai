"""Evidence-first educational pipeline; never computes estate distributions."""
import json
import re
import unicodedata
import requests
from backend.llm import provider
from backend.rag.fiqh.retriever import retrieve_fiqh
from backend.rag.fiqh.vector_store import load_chunks
from backend.rag.retriever import RULES_PATH
from backend.rag.source_validation import validate_rule_records
from backend.sources.router import enrich_sources
from backend.schemas.response import Concept, EducationalResponse
from backend.rules.educational_concepts import supported_concepts, minimal_answer


def detect_language(question: str) -> str:
    return "ar" if re.search(r"[\u0600-\u06ff]", question) else "en"


def educational_query(question: str) -> str:
    """Disambiguate short terms for retrieval, without changing source text."""
    if "residu" in question.lower() or "عصب" in question or "تعصيب" in question:
        terms = "العصبة صاحب فرض الباقي كل التركة"
        if "الفرض" in question or "fixed" in question.lower():
            terms += " الفروض المقدرة"
        return terms
    elif "fixed" in question.lower() or "الفروض" in question:
        terms = "الميراث تعريف الفرض وأصحاب الفروض"
    else:
        terms = "نظام المواريث في الإسلام"
    return terms + "\n" + question


def inheritance_section_filter() -> dict:
    # Use the existing Qdrant section filter only when approved metadata
    # unambiguously identifies a single inheritance article. No guessed title.
    sections = {c.get("section") for c in load_chunks() if c.get("section")}
    matching = []
    for section in sections:
        title = "".join(c for c in unicodedata.normalize("NFD", section)
                        if not unicodedata.combining(c)).strip()
        if title in {"ارث", "ميراث", "الميراث", "المواريث"}:
            matching.append(section)
    return {"section": matching[0]} if len(matching) == 1 else {}


def retrieve_educational_evidence(question: str) -> list[dict]:
    filters = inheritance_section_filter()
    # A comparison needs evidence for both concepts, within the same three-hit
    # budget. This uses the existing retriever, not a second ranking stage.
    lower = question.lower()
    if (("تعصيب" in question or "residu" in lower)
            and ("الفرض" in question or "fixed" in lower)):
        residue = retrieve_fiqh("العصبة صاحب فرض الباقي كل التركة", top_k=2, filters=filters)
        fixed = retrieve_fiqh("الفروض المقدرة النصف والربع والثمن والثلثان والثلث والسدس", top_k=1, filters=filters)
        return residue + fixed
    return retrieve_fiqh(educational_query(question), top_k=3, filters=filters)


def collect_excerpts(hits: list[dict]) -> list[dict]:
    excerpts, seen = [], set()
    for hit in hits:
        for part in (hit, hit.get("previous_chunk"), hit.get("next_chunk")):
            if not part:
                continue
            source = part.get("original_source", part["source"])
            identity = source["chunk_id"]
            if identity in seen:
                continue
            seen.add(identity)
            excerpts.append({"evidence_id": identity, "text": part["text"],
                "source_name": source["source_name"], "section": source.get("section"),
                "reference": {"volume": source.get("volume"), "page": source.get("page")},
                "source_url": source["source_url"], "immutable_text": True,
                "provenance": source})
            if "original_source" in part and isinstance(part["source"].get("char_start"), int):
                excerpts[-1].update(excerpt_char_start=part["source"]["char_start"],
                                    excerpt_char_end=part["source"]["char_end"])
    return excerpts


def build_evidence_bundle(hits: list[dict], max_characters: int = 5000) -> list[dict]:
    """Keep main hits and at most one useful neighbor; copy exact substrings.

    Offsets remove overlap only within the same immutable source document.
    Provenance retains the original chunk; excerpt offsets describe the slice.
    """
    candidates = [{**hit, "previous_chunk": None, "next_chunk": None} for hit in hits]
    if hits:
        first = hits[0]
        previous = first.get("previous_chunk")
        if (previous and len(first["text"]) < 1200
                and previous["source"].get("section") == first["source"].get("section")):
            # The trailing paragraph bridges a main hit that starts mid-discussion.
            # Keep that exact paragraph, rather than unrelated earlier paragraphs.
            matches = list(re.finditer(r"[^\n]+(?:\n(?!\n)[^\n]+)*", previous["text"]))
            if matches:
                match = matches[-1]
                source = dict(previous["source"])
                if isinstance(source.get("char_start"), int):
                    source["char_start"] += match.start()
                    source["char_end"] = source["char_start"] + len(match.group())
                previous = {**previous, "text": match.group(), "source": source,
                            "original_source": previous["source"]}
            candidates.insert(0, previous)
    bundle, seen_text, covered = [], set(), {}
    remaining = max_characters
    for excerpt in collect_excerpts(candidates):
        source, text = excerpt["provenance"], excerpt["text"]
        if text in seen_text or remaining <= 0:
            continue
        seen_text.add(text)
        document = (source.get("input_file"), source.get("document_sha256"))
        start = excerpt.get("excerpt_char_start", source.get("char_start"))
        segments = [(0, len(text))]
        if all(document) and isinstance(start, int):
            for left, right in covered.get(document, []):
                segments = [(a, b) for lo, hi in segments
                            for a, b in ((lo, min(hi, left - start)),
                                         (max(lo, right - start), hi)) if a < b]
        for lo, hi in segments:
            hi = min(hi, lo + remaining)
            if hi <= lo:
                continue
            part = {**excerpt, "evidence_id": f"E{len(bundle) + 1}", "text": text[lo:hi]}
            if isinstance(start, int):
                part.update(excerpt_char_start=start + lo, excerpt_char_end=start + hi)
                if all(document):
                    covered.setdefault(document, []).append((start + lo, start + hi))
            bundle.append(part)
            remaining -= hi - lo
    return bundle


def validate_citations(generated: dict, bundle: list[dict]) -> tuple[str, list[Concept], set[str]]:
    if generated.get("status") == "insufficient_evidence" or generated.get("supported") is False:
        raise ValueError("insufficient_evidence")
    answer = generated["answer"]
    concepts = [Concept.model_validate(c) for c in generated.get("key_concepts", [])]
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Explanation is empty")
    prose = answer + " " + " ".join(c.term + " " + c.explanation for c in concepts)
    ids = set(re.findall(r"\[(E[^\]\s]*)\]", prose))
    ids.update(re.findall(r"\bE[0-9]+\b", prose))
    # Accept legacy ID lists too, but validate every declared reference.
    declared = generated.get("evidence_ids", [])
    if not isinstance(declared, list) or any(not isinstance(i, str) for i in declared):
        raise ValueError("Invalid citation list")
    ids.update(declared)
    known = {e["evidence_id"] for e in bundle}
    if ids - known:
        raise ValueError("Unknown evidence IDs: " + ", ".join(sorted(ids - known)))
    if not ids:
        raise ValueError("Explanation claims support without a valid evidence citation")
    if re.search(r'[«»“”"\u06dd]|\b\d{1,3}:\d{1,3}\b', prose):
        raise ValueError("Generated quotations or source references are not allowed")
    return answer, concepts, ids


def run_learn(question: str) -> dict:
    language = detect_language(question)
    response = EducationalResponse(mode="learn", decision_state="specialist_referral",
        language=language, answer=("لا تكفي الأدلة المتاحة لتقديم شرح موثق لهذا السؤال." if language == "ar"
        else "The available evidence is insufficient for a sourced explanation of this question."))
    if not question.strip():
        response.decision_state = "needs_clarification"
        response.clarification_question = "ما سؤالك عن المواريث؟" if language == "ar" else "What would you like to learn about inheritance?"
        return response.model_dump()
    try:
        response.source_excerpts = build_evidence_bundle(retrieve_educational_evidence(question))
    except (RuntimeError, ValueError, OSError) as exc:
        response.limitations.append("Evidence retrieval unavailable: " + str(exc))
    if not response.source_excerpts:
        response.limitations.append("No matching approved fiqh evidence is available.")
        return response.model_dump()
    # Quran references come only from existing validated rules. Quran text is
    # never sent to the explainer, and is attached only after reasoning.
    evidence = [{k: e[k] for k in ("evidence_id", "text", "source_name", "section", "source_url")}
                for e in response.source_excerpts]
    concept_metadata = supported_concepts(question, language, evidence)
    try:
        generated = provider.explain(question, language, evidence)
        answer, concepts, ids = validate_citations(generated, response.source_excerpts)
        response.answer, response.key_concepts = answer, concepts
        response.decision_state = "ready"
        response.source_excerpts = [e for e in response.source_excerpts if e["evidence_id"] in ids]
    except requests.Timeout:
        # Only source-bound definitions covering all requested concepts qualify.
        comparison = "الفرق" in question or "difference" in question.lower()
        if concept_metadata and (not comparison or len(concept_metadata) == 2):
            response.answer = minimal_answer(concept_metadata)
            response.key_concepts = [Concept(term=c["term"], explanation=c["explanation"] + " [" + c["evidence_id"] + "]") for c in concept_metadata]
            response.decision_state = "ready"
            response.limitations.append("Qwen timed out; returned a minimal source-bound concept explanation.")
        else:
            response.limitations.append("Explanation timed out; no matching structured concept metadata is available for a safe fallback.")
    except (ValueError, KeyError, TypeError, requests.RequestException) as exc:
        response.limitations.append("Explanation withheld: " + str(exc))
    response.sources = [e["provenance"] for e in response.source_excerpts]
    # Attach Quran only when an exact reference occurs in retrieved source text.
    rules = validate_rule_records(json.loads(RULES_PATH.read_text(encoding="utf-8")))
    refs = set(re.findall(r"(?<![0-9])[0-9]{1,3}:[0-9]{1,3}(?![0-9])", " ".join(e["text"] for e in response.source_excerpts)))
    selected = [r for r in rules if r["source"]["reference"] in refs]
    attached_references = set()
    for rule in enrich_sources(selected):
        source = rule["source"]
        reference = source.get("reference")
        if reference in attached_references:
            continue
        attached_references.add(reference)
        response.sources.append(source)
        if source.get("arabic_text") and source.get("immutable_text") is True:
            response.source_excerpts.append({"text": source["arabic_text"], "source_name": source["source_name"],
                "section": None, "reference": source["reference"], "source_url": source.get("source_url"), "immutable_text": True})
    response.limitations.append("Coverage is limited to the approved local corpus; page numbers may be unavailable. Evidence-ID checks do not prove every generated claim.")
    return response.model_dump()


if __name__ == "__main__":
    print(json.dumps(run_learn(input("السؤال: ")), ensure_ascii=False, indent=2))
