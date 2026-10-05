"""Conservative evidence-local text checks; no concept rules or LLM verifier.

This is a lexical safety screen, not a proof of semantic entailment. Short
source statements are compared individually to avoid borrowing vocabulary from
unrelated paragraphs. Uncertain statements are omitted, not rewritten.
"""
from difflib import SequenceMatcher
import re

from backend.pipeline.claim_guard import _units, _FRACTIONS
from backend.rules.educational_concepts import matching_text

_PRESENTATION = set('هو هي هم هذا هذه ذلك يكون تكون يعني تعني المقصود اصطلاحا لغة في من على الى عن مع ما والذي التي حيث كما بحسب وفق وفقا الدليل الادلة المرفقة عند عندما ان بين اما بينما وهو وهي the a an is are means of to in from with according evidence'.split())


def words(text):
    text = matching_text(re.sub(r'\[(?:E\d+|\d+)\]', '', text).casefold())
    result = []
    for word in re.findall(r'[a-z]+|[\u0621-\u064a]+|\d+(?:/\d+)?', text):
        if word in _PRESENTATION:
            continue
        if word.startswith('لل'):
            word = word[2:]
        else:
            if word.startswith(('وال', 'فال', 'بال', 'كال')):
                word = word[1:]
            if word.startswith('ال'):
                word = word[2:]
        if word not in _PRESENTATION:
            result.append('NEG' if word in {'لا','لم','لن','ليس','عدم','not','no','without'} else word)
    return result


def _similar(word, other):
    if word == other:
        return True
    if not re.fullmatch(r'[\u0621-\u064a]+', word + other):
        return word.rstrip('s') == other.rstrip('s')
    if len(word)==len(other)==3 and word[0] in 'اي' and other[0] in 'اي' and word[1:]==other[1:]:
        return True
    matcher = SequenceMatcher(None, word, other)
    return min(len(word), len(other)) >= 4 and matcher.ratio() >= .66 and sum(b.size for b in matcher.get_matching_blocks()) >= 3


def _supported(sentence, passages, context_words=()):
    tokens = words(sentence)
    if not tokens:
        return False
    # A source heading may supply the sentence subject, while its short
    # definition appears on the following line. Never borrow predicate words.
    if len(tokens)>3 and tokens[0] in context_words:
        tokens = tokens[1:]
    for passage in passages:
        candidates = words(passage)
        if not candidates:
            continue
        matched = sum(any(_similar(t, c) for c in candidates) for t in tokens)
        if ('NEG' in tokens) != ('NEG' in candidates):
            continue
        qualifier = r'\b(?:اذا|عند|عندما|بشرط|الا|if|when|unless|except)\b'
        if re.search(qualifier, matching_text(passage)) and not re.search(qualifier, matching_text(sentence)):
            continue
        # Permit a subject label / natural paraphrase, but not a new clause.
        if matched / len(tokens) >= .75 and len(tokens) - matched <= 1:
            return True
    return False


def check_sentences(answer, evidence, declared_ids=()):
    known = {e['evidence_id']: e['text'] for e in evidence}
    kept, removed = [], []
    units = [clause for sentence in _units(answer)
             for clause in re.split(r'،\s+(?=(?:وهو|وهي|كما|بينما|اما|أما|لكن)\b)', sentence)]
    for sentence in units:
        ids = set(re.findall(r'\[(E\d+)\]', sentence)) or set(declared_ids)
        passages = [p.strip() for i in ids if i in known
                    for p in re.split(r'\n+|(?<=[.؛!?؟])\s+', known[i])
                    if p.strip() and len(words(p)) <= 90]
        # A copular definition can be followed by additional behavior. Keep
        # its complete introductory clause as an anchor, not the later rules.
        introductions = [p.split('،',1)[0] for p in passages if '،' in p and
                         re.search(r'\b(?:هو|هي|اصطلاحا)\b', matching_text(p.split('،',1)[0])) and
                         not re.match(r'(?:اذا|عند|بشرط|الا|ما عدا|ان)\b', matching_text(p.split('،',1)[1]).strip()) and
                         len(words(p.split('،',1)[0]))>=3]
        context_words = {w for i in ids if i in known for w in words(known[i])}
        if _supported(sentence, passages + introductions, context_words):
            kept.append(sentence)
        else:
            removed.append({'sentence': sentence, 'reason': 'uncertain_sentence_support'})
    return '\n'.join(kept), removed


def check_consistency(answer):
    """Only explicit count/list and identical-subject numeric contradictions."""
    kept, removed, fractions = [], [], {}
    numbers = {'قسمان': 2, 'قسمين': 2, 'نوعان': 2, 'نوعين': 2, 'فئتان': 2, 'فئتين': 2, 'ثلاثة': 3, 'ثلاث': 3,
               'اربعة': 4, 'اربع': 4, 'اثنان': 2, 'اثنين': 2,
               'two': 2, 'three': 3, 'four': 4}
    for sentence in _units(answer):
        text = matching_text(re.sub(r'\[E\d+\]', '', sentence).casefold())
        for label, value in _FRACTIONS.items():
            text = re.sub(r'\b'+re.escape(label)+r'\b', value, text)
        reason = None
        # Inspect only an explicit colon-led enumeration in the same sentence.
        if ':' in text:
            prefix, listing = text.split(':', 1)
            count = next((n for word, n in numbers.items() if word in prefix.split()), None)
            items = [p.strip(' .') for p in re.split(r'،|,|\s+and\s+', listing) if p.strip(' .')]
            if count is not None and len(items) > 1 and len(items) != count:
                reason = 'inconsistent_explicit_list_count'
        # Different conditional sentences are not contradictory allocations.
        match = re.fullmatch(r'(.{2,80}?)\s+(\d+/\d+)\s*[.]?', text.strip())
        if match:
            subject, value = match.groups()
            if subject in fractions and fractions[subject] != value:
                reason = 'contradictory_same_subject_fraction'
            fractions[subject] = value
        if reason:
            removed.append({'sentence': sentence, 'reason': reason})
        else:
            kept.append(sentence)
    return '\n'.join(kept), removed
