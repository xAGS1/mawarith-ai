"""Conservative educational scope checks and exact public evidence slices.

These checks never determine inheritance shares. They do not constitute a
general semantic proof of every generated claim.
"""
import re
from backend.rules.educational_concepts import matching_text


def check_concept_scope(question: str, answer: str, cited: list[dict]) -> None:
    broad = ("اصحاب الفروض", "fixed-share heirs", "fixed share heirs")
    narrow = ("اصحاب الفروض النسبية", "اصحاب الفروض السببية", "consanguine fixed-share heirs", "fixed-share heirs by blood")
    query = matching_text(question.lower())
    prose = matching_text(answer.lower())
    if not any(term in query or term in prose for term in broad):
        return
    if any(term in query for term in narrow):
        # Even a narrow question cannot license a broader unqualified answer.
        if any(term in prose for term in narrow):
            return
    paragraphs = [matching_text(p.lower()) for e in cited
                  for p in re.split(r"\n\s*\n", e["text"])]
    narrower = any(any(term in p for term in narrow) for p in paragraphs)
    broad_support = any(re.search(r"(?:اصحاب الفروض|fixed[- ]share heirs)\s+(?:هم|من|الورثة|are|include|means)\b", p) and
                        not any(term in p for term in narrow) for p in paragraphs)
    if narrower and not broad_support:
        raise ValueError("Retrieved evidence covers a narrower concept, not the requested broader definition")


def relevant_public_excerpts(question: str, excerpts: list[dict]) -> list[dict]:
    """Select whole matching paragraphs; never paraphrase or cut sentences.

    Short evidence remains intact. Large evidence without a confidently matched
    paragraph is omitted from public display, retaining its source metadata.
    Quran adapter text is always kept intact.
    """
    query = matching_text(question.lower())
    anchors = []
    for terms in (("اصحاب الفروض", "fixed-share heirs", "fixed share heirs"),
                  ("عصبة", "تعصيب", "residu"), ("الفرض", "fixed share")):
        if any(term in query for term in terms):
            anchors.extend(terms)
    output = []
    for excerpt in excerpts:
        text = excerpt["text"]
        if len(text) <= 900 or excerpt.get("source_type") == "quran":
            output.append(excerpt)
            continue
        paragraphs = list(re.finditer(r"[^\n]+(?:\n(?!\s*\n)[^\n]+)*", text))
        selected = [p for p in paragraphs if any(a in matching_text(p.group().lower()) for a in anchors)]
        # Keep intervening source context, never splice unrelated passages.
        if not selected:
            continue
        start, end = selected[0].start(), selected[-1].end()
        if end - start > 1200:
            continue
        public = {**excerpt, "text": text[start:end]}
        origin = excerpt.get("excerpt_char_start", excerpt.get("provenance", {}).get("char_start"))
        if isinstance(origin, int):
            public.update(excerpt_char_start=origin + start, excerpt_char_end=origin + end)
        output.append(public)
    return output
