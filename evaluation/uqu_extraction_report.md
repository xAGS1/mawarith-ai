# UQU extraction check

## Root cause and method

The PDF renders correctly, but several embedded `ToUnicode` character maps are
wrong. Plain pypdf 5.9.0, PyMuPDF 1.28.2 and pdfplumber 0.11.10 reproduced the
corruption; changing libraries alone did not fix it. pdfplumber additionally
reversed Arabic reading order. PyMuPDF split fractions and reversed some
multi-character Arabic ligatures. pypdf provided the best logical Arabic order.

Production now uses pypdf after in-memory character-map recovery from the
embedded TrueType Unicode cmap, via fontTools. Only Identity-H fonts with
identity CID-to-glyph mapping and unambiguous Unicode mappings are repaired.
Unknown/custom glyph mappings remain unchanged. Arabic presentation glyphs are
decomposed using Unicode compatibility mappings; Arabic digits are decoded to
equivalent Western digits before bidi processing so `12` does not become `21`.
There are no word replacements, LLM corrections or invented source passages.
The raw PDF bytes and approved document hash remain unchanged.

## Manual page checks

Page numbers below are PDF indices; printed folios are one less.
The original rendered pages were inspected, alongside all three extractors.

| Section | PDF page | Before | Recovered excerpt |
| --- | --- | --- | --- |
| العول | 22 | `تعريفو` / `أصل الدسألة` / `نضعو` | `تعريفه:  لغة: الزيادة. واصطلاحا: زيادة في الفروض ينتج عنها زيادة في أصل المسألة.` |
| التعصيب | 13 | `تعريفو` / `الإحاطة` context corrupted | `اصطلاحا: الإرث بغير تقدير.` |
| الحجب | 13 | `منع الوارث من الإرث كلو أو بعضو` | `منع الوارث من الإرث كله أو بعضه` |
| الرد | 23 | `نلاحظ أنو بقي` / `الباقي وىو` | `واصطلاحا: بقاء مال من التركة بعد قسمتها.` |
| أصحاب الفروض / الفرض | 7 | `ٔ/ٕ` / `ٔ/ٛ` | `1/2` / `1/8`; `واصطلاحا:  الإرث بتقدير.` |
| Terminology appendix | 28 | damaged letters in definition entries | `الفرض : هو نصيب مقدر شرعا لوارث مخصوص، لا يزيد إلا بالرد ولا ينقص إلا بالعول` |

Awl, before (unmodified pypdf extraction):

```text
تعريفو: لغة: الزيادة. واصطلاحا: زيادة في الفروض ينتج عنها زيادة في أصل الدسألة.
طريقة الحل: نجمع السهام، وما نتج فهو أصل الدسألة، ونضعو بدل الأصل الذي استخرجناه.
 ٙ/ ٛ
ٔ/ٕ زوج ٖ
ٔ/ٕ أخت ش ٖ
ٔ/ٖ أم  ٕ
```

Awl, recovered:

```text
تعريفه:  لغة: الزيادة. واصطلاحا: زيادة في الفروض ينتج عنها زيادة في أصل المسألة.
طريقة الحل: نجمع السهام، وما نتج فهو أصل المسألة، ونضعه بدل الأصل الذي استخرجناه.
 6 /8
1/2 زوج  3
1/2 أخت ش 3
1/3 أم 2
```

## Corpus and indexing

All 28 pages are retained in ignored `processed/pages.json`, with document,
page-text and excerpt hashes, offsets, extraction version and quality flags.
Two pages (3 and 15) retain substantial unrecoverable glyph corruption. They are
quarantined from retrieval and indexing, without guessing their contents.
They require further font/OCR review. This is not certification of every table
or Quran passage printed inside the PDF. Complex table reading order and some
spacing/bracket layout remain imperfect; actual source typos are preserved.

The final eligible corpus contains **47 chunks**. Raw PDF, processed JSON and
comparison/rendering artifacts remain git-ignored.

Qdrant initially contained only `mawarith_fiqh`. UQU was previously embedded
from the PDF in memory by production retrieval. Its recovered corpus is now
also indexed in the isolated `mawarith_uqu` collection, **47 points**. Existing
production retrieval continues using the improved local extractor; no source
routing architecture was changed. Kuwaiti `mawarith_fiqh` remains at **1,707
points** and was never targeted by indexing/deletion calls.

Synchronization upserts first, verifies every replacement ID, then deletes
only stale `source_id=uqu_mawarith_1` records in the UQU collection. A failed
or incomplete upsert cannot prune old records.

Reproduce:

```powershell
python -m backend.rag.rebuild_uqu --index
python evaluation/check_uqu_extraction_live.py
```

## Live answer verification

The five requested questions are executed through production `run_request`,
real local BGE-M3/Qdrant retrieval, and the unchanged Qwen model. Full responses,
source excerpts, selected provenance, generated output and guard traces are in
`evaluation/uqu_extraction_live.json`.

The recovered excerpts and answers no longer contain the reported encoding
errors. Awl and fixed-share explanations reproduce the supported definitions.
However, extraction repair does **not** resolve existing generation/grounding
errors: the العصبة answer adds an unsupported “الأحقية المادية” explanation
and miscounts its categories; الرد adds a misleading explanatory clause;
الحجب overgeneralizes personal blocking. These are recorded failures of the
unchanged explanation/guard behavior, not approved religious statements.
Do not interpret an API `supported` flag as a manual grounding pass here.

## Validation and scope

Focused extraction, synchronization, definition and learning tests: **78 passed**.
Full backend suite: **470 passed**. Python compilation checks passed.
Tests cover exact recovered definitions, numeric order, old corrupt patterns,
hash preservation, ambiguous cmap rejection, quarantine and safe source-only
indexing, including incomplete-upsert protection.

No solver, executable rule, model/configuration, request-understanding, claim
guard, Quran adapter, frontend or API schema changes were made in this task.

Files changed for this task:

- `backend/rag/uqu_extraction.py` (new)
- `backend/rag/rebuild_uqu.py` (new)
- `backend/learning/definition_retrieval.py`
- `backend/rag/educational_context.py` (skip quarantined extraction pages)
- `requirements.txt` (fontTools dependency)
- `tests/test_uqu_extraction.py` (new)
- `tests/test_uqu_rebuild.py` (new)
- `evaluation/check_uqu_extraction_live.py` (new)
- `evaluation/uqu_extraction_live.json` (new)
- `evaluation/uqu_extraction_report.md` (new)

PyMuPDF/pdfplumber were installed for comparison only; production does not
require them. Other worktree changes predate this task.
