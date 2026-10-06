"""Light Fanar-only hard-error checks; not a semantic entailment verifier."""
import re
from backend.pipeline.claim_guard import _units
from backend.pipeline.educational_sentence_check import words
from backend.rules.educational_concepts import matching_text


def check_cited_support(answer,evidence,declared_ids=()):
    known={e['evidence_id']:e for e in evidence}
    kept,removed=[],[]
    for sentence in _units(answer):
        ids=set(re.findall(r'\[(E\d+)\]',sentence)) or set(declared_ids)
        cited=[known[i] for i in ids if i in known]
        reason=None
        if not cited or ids-known.keys():
            reason='missing_or_invalid_sentence_citation'
        elif re.search(r'\b(?:اجمع|اجماع|consensus|unanimously)\b',matching_text(sentence.casefold())):
            if not any(re.search(r'\b(?:اجمع|اجماع|consensus|unanimously)\b',matching_text(e['text'].casefold())) for e in cited):
                reason='unsupported_consensus_attribution'
        if reason is None:
            claim=words(sentence)
            positive=[w for w in claim if w!='NEG']
            for e in cited:
                for passage in re.split(r'\n+|(?<=[.؛!?؟])\s+',e['text']):
                    source=words(passage)
                    content=[w for w in source if w!='NEG']
                    # Exact predicate opposition is an obvious contradiction.
                    # No lexical threshold is used to require paraphrase copying.
                    if len(positive)>=3 and positive==content and ('NEG' in claim)!=('NEG' in source):
                        reason='explicit_opposite_negation'
        if reason:
            removed.append({'sentence':sentence,'reason':reason})
        else:
            kept.append(sentence)
    return '\n'.join(kept),removed
