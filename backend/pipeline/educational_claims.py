"""Lightweight clear-error checks, not an exact-text paraphrase verifier."""
import re
from fractions import Fraction
from backend.rules.educational_concepts import matching_text
from backend.pipeline.claim_guard import _units, _FRACTIONS

_SUBJECTS = (
    (r"(?:ال)?اخ(?: الشقيق| لاب| لام)?\b|\bbrother\b", ("اخ", "اخوة", "اخوان", "brother")),
    (r"(?:ال)?اخت(?: الشقيقة| لاب| لام)?\b|\bsister\b", ("اخت", "اخوات", "sister")),
    (r"(?:ال)?زوجة\b|\bwife\b", ("زوجة", "زوجات", "لهن", "wife")),
    (r"(?:ال)?ام\b|\bmother\b", ("ام", "ابويه", "mother")),
    (r"(?:ال)?بنت\b|\bdaughter\b", ("بنت", "بنات", "اولاد", "daughter")),
    (r"(?:ال)?ابن\b|\bson\b", ("ابن", "ابناء", "اولاد", "son")),
)
_ENTITLEMENT = re.compile(r"ياخذ|تاخذ|يحصل|تحصل|نصيب|يرث|ترث|يستحق|تستحق|receives?|takes?|share", re.I)


def filter_claims(answer, evidence, declared_ids=()):
    known = {e["evidence_id"]: e for e in evidence}
    kept, blocked = [], []
    for sentence in _units(answer):
        ids = set(re.findall(r"\[(E\d+)\]", sentence)) or set(declared_ids)
        support = [known[i]["text"] for i in ids if i in known]
        normalized = matching_text(sentence.casefold())
        context = matching_text(" ".join(support).casefold())
        # Cited sentences can paraphrase freely; citation IDs never grant new
        # heir entitlements or shares absent from that sentence's cited source.
        reason = None
        if ids - known.keys() or not support:
            reason = "missing_or_invalid_sentence_citation"
        if _ENTITLEMENT.search(normalized):
            for pattern, aliases in _SUBJECTS:
                if re.search(pattern, normalized):
                    if not any(a in context for a in aliases):
                        reason = "heir_not_supported_by_cited_evidence"
                    fractions = [name for name in _FRACTIONS if re.search(r"\b"+name+r"\b", normalized)]
                    fractions.extend(re.findall(r"\d+\s*/\s*\d+", normalized))
                    for fraction in fractions:
                        # Match subject and fraction in the same short source
                        # statement, not unrelated clauses in a large chunk.
                        direct = False
                        for source in support:
                            for part in re.split(r"\n|[.؛]", matching_text(source.casefold())):
                                if len(part) > 400:
                                    continue
                                value = _FRACTIONS.get(fraction, fraction)
                                if any(a in part for a in aliases) and (fraction in part or value in part):
                                    # A narrower relation cannot license an
                                    # unqualified sibling/child entitlement.
                                    qualifications = ("لاب", "لام", "شقيق", "بنت ابن")
                                    if not any(q in part and q not in normalized for q in qualifications):
                                        direct = True
                        if not direct:
                            reason = "share_not_directly_supported_for_this_heir"
        for name, fraction in _FRACTIONS.items():
            if re.search(r"\b" + name + r"\b", normalized) and name not in context and fraction not in context:
                reason = "share_absent_from_cited_evidence"
        for number in re.findall(r"\d+\s*/\s*\d+|\d+\s*%", sentence):
            if number.replace(" ", "") not in context.replace(" ", ""):
                reason = "number_absent_from_cited_evidence"
        for term in ("العول", "الرد", "محجوب", "حجب الحرمان"):
            if term in normalized and term not in context:
                reason = "rule_absent_from_cited_evidence"
        if reason:
            blocked.append({"sentence": sentence, "reason": reason})
        else:
            kept.append(sentence)
    return "\n".join(kept), blocked


def without_internal_ids(text):
    return re.sub(r"\s*\[(?:E\d+|\d+)\]", "", text).strip()


def filter_calculation_prose(answer, result):
    """Numerical explanation must match the named heir's verified allocation."""
    allocations = {}
    for share in result.get("shares", []):
        allocations.setdefault(matching_text(share["heir"]), set()).add(Fraction(share["fraction"]))
    for share in result.get("post_tasil", {}).get("distribution", []):
        allocations.setdefault(matching_text(share["heir"]), set()).add(Fraction(share["per_head_shares"]))
    kept = []
    for sentence in _units(answer):
        text = matching_text(without_internal_ids(sentence))
        try:
            fractions = [Fraction(f.replace(" ", "")) for f in re.findall(r"-?\d+\s*/\s*\d+", text)]
        except (ValueError, ZeroDivisionError):
            continue
        fractions.extend(Fraction(value) for name,value in _FRACTIONS.items() if re.search(r"\b"+name+r"\b", text))
        named = [r for r in allocations if re.search(r"(?<!\w)(?:ال)?" + re.escape(r) + r"(?!\w)", text)]
        if fractions and (len(named) != 1 or any(f not in allocations[named[0]] for f in fractions)):
            continue
        if re.search(r"\d+\s*%|\d+\.\d+", text):
            continue  # Display percentages only from the verified table.
        kept.append(sentence)
    return "\n".join(kept)
