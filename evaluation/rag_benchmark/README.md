# Retrieval benchmark

Run from the repository root with the existing backend environment:

```powershell
.venv/Scripts/python.exe -X utf8 evaluation/rag_benchmark/run_retrieval_benchmark.py
```

Uses existing BGE-M3 and Qdrant settings and the current `mawarith_fiqh` collection. No LLM, ingestion, collection replacement, or final-answer evaluation. Questions are evaluation inputs only; never ingest this folder.

Timestamped JSON under `results/` contains ranked hits, scores, source metadata, previews, neighbor IDs, and review flags. Recall@1/3/5 is macro recall over explicitly pinned gold chunk IDs only. Neighbors are excluded. Lexical topic checks for questions without gold IDs are diagnostic heuristics, not accuracy measurements. Gold definitions are a small reviewed sample, not exhaustive relevance judgments: alternative relevant passages may be missed by this metric. Duplicate detection uses normalized equality or ≥90% sequence similarity. Split-condition flags are review candidates, not automated judgments of religious meaning. Per-question failures are recorded and count as misses for gold questions.

If Qdrant is unavailable, the runner saves an unavailable report with null metrics and exits cleanly with code 1. Restore the existing service and collection, then rerun the command above; this script never creates or reindexes a collection.

## Demo prompts

Three learn questions (curated original passages, not invented summaries):

- ما معنى أصحاب الفروض؟
- ما معنى الحجب؟
- ما معنى التركة؟

Two comparisons (separate source text for each concept):

- ما الفرق بين الفرض والتعصيب؟
- ما الفرق بين العول والرد؟

Two cases within existing deterministic coverage:

- توفي رجل وترك زوجة وأم وابنين وبنت.
- توفي رجل وترك زوجة وابن وبنت.

One ambiguous case (expect clarification about brother subtype, not a guessed distribution):

- توفي رجل وترك بنتًا وأخًا.

Source selection: six newly pinned definitions use the approved Kuwaiti Fiqh Encyclopedia volume 3 corpus. Exact passages, offsets, hash, and provenance live in `backend/learning/curated_source_passages.json`. Estate retains the majority-school qualification; radd retains relative fixed-share heirs and absence of another entitlement. No new calculation rules are derived. Existing fixed-share/residuary gold chunks remain unchanged.

## Initial run: 2026-10-05

All 24 queries completed against the existing 1,707-point collection. Ten questions have pinned gold targets: Recall@1 **0.25**, Recall@3 **0.35**, Recall@5 **0.35**. These measure exact target-chunk retrieval, not answer correctness or all possible relevant evidence.

Gold-target misses: fixed-share heirs, fixed share, residuary heirs, awl, case origin, and fixed-share/residuary comparison (q01, q02, q03, q05, q08, q09). Awl retrieved unrelated material in its top five; case origin and the comparison also ranked unrelated entries highly. q01 ranked the narrower relative-fixed-share-heirs passage above the general category passage. This confirms the need for the curated-first path.

Additional lexical flags: blocking-type comparison, wife's eighth, and six prescribed fractions (q11, q14, q15). **q11 is a lexical false negative:** a relevant blocking-types passage was retrieved at rank 3, using “حجب حرمان” rather than the exact anchor “حجب الحرمان”. Treat these flags as review queues, not certified relevance labels.

Sixteen queries have possible boundary/continuation flags; none have ≥90% whole-chunk duplicates. Manual corpus review confirms that the general fixed-share-heirs enumeration spans adjacent chunks; the blocking heading is separated from its technical definition; and radd's “two conditions” introduction is separated from those conditions. Neighbor IDs are recorded to support further review. No chunking, embedding, filters, or collection changes were made.

Full results: `results/retrieval_20261005T082517_502032Z.json`.

## Minimal retrieval improvement

Same-language canonical concept terms are appended to the original question before embedding. Whole-alias matching normalizes diacritics and handles attached Arabic conjunctions; longer matches prevent “أصحاب الفروض” from becoming a separate “الفرض” match. Aliases reuse the concept catalog, with the existing “الفروض المقدرة” and “التعصيب / residuary inheritance” terminology. No definitions or rulings are generated as expansions.

For matched concepts with verified, consistent section provenance, use the existing Qdrant section filter. Explicit caller filters are preserved; missing/unverified/disagreeing provenance keeps unrestricted retrieval. The existing neighbor fields remain unchanged. No automatic neighbor merge was added: condition-to-ruling dependency cannot safely be decided from adjacency alone.

An English-label expansion of Arabic questions reduced recall and was discarded. The retained Arabic-only/section-aware variant completed the identical 24 questions with the existing model, collection, and gold targets:

| Metric | Before | After |
| --- | ---: | ---: |
| Recall@1 | 25% | 30% |
| Recall@3 | 35% | 35% |
| Recall@5 | 35% | 35% |

Gold-question comparison (rank of retrieved gold chunk; “miss” means outside top five):

| Question | Before | After |
| --- | --- | --- |
| q01 أصحاب الفروض | miss | miss |
| q02 الفرض | miss | miss |
| q03 العصبة | miss | miss |
| q04 الحجب | 3 | **1** |
| q05 العول | miss | miss |
| q06 الرد | 1 | 1 |
| q07 التركة | 1 | 1 |
| q08 أصل المسألة | miss | miss |
| q09 الفرض والتعصيب | miss | miss |
| q10 العول والرد | 1 | **2** |

Unjudged questions: q11, q12, q15, and q20 changed ranked results; there is no gold basis for claiming an accuracy improvement or regression. q13, q14, q16, q17, q18, q19, q21, q22, q23, and q24 retained identical ranked chunk IDs. q15 now passes the lexical topic check. Remaining review flags: q01, q02, q03, q05, q08, q09, q11, q14. The earlier caveat about q11's lexical false negative still applies.

The five requested weak concepts and the fixed-share/residuary comparison still need retrieval work. This small improvement does not resolve the known chunk-boundary issues or claim demo-wide retrieval readiness.

Final results: `results/retrieval_20261005T083453_756167Z.json`. Validation: 61 focused RAG tests and 345 full backend tests passed. No ingestion, collection, source-text, solver, model, frontend, claim-guard, or API changes.
