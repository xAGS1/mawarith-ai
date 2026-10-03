# mawarith-ai
MAWARITH AI is an Arabic-first intelligent Islamic inheritance reasoning system with structured heir parsing, source-grounded fiqh retrieval, deterministic verification, and explainable inheritance calculations.

## Current pipeline

```text
Question -> Qwen relation parser -> Shared factual case features
         -> Shared condition-aware local rule retriever -> Shared source coverage gate
         -> Shared QuranEnc source enrichment (exact text, cached locally)
         -> Shared Fiqh RAG evidence retrieval (support only)
         -> Qwen reasoner only when coverage is sufficient
         -> Shared Python fraction verifier -> Final JSON with sources
```

With Ollama running and `qwen3:8b` installed, run from the project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m backend.pipeline.qwen_pipeline
```

Output includes `question`, `parsed_relations`, `case_features`, `sources`,
`source_coverage`, `decision_state` and `result`. When any mentioned relation has
no retrieved rule with matching `applies_to` and satisfied conditions, Python returns `insufficient_sources` with
`result: null` and skips both reasoning and verification. Otherwise the state is
`ready` and reasoning runs followed by verification. An empty parsed case is blocked.

The CLI currently demonstrates the wife/full-brother case, which should be blocked
because the source library has no rule for the brother. Coverage measures distinct
relation names, not head counts, and checks availability rather than legal completeness.
The model-independent modules under `backend/rules/`, `backend/rag/`,
`backend/verifier/` and `backend/schemas/` do not import Qwen.

The shared `backend/sources/` layer fetches Arabic Quran text independently from
QuranEnc and preserves it exactly in `sources[].source.arabic_text`, alongside
`provider`, `reference`, `immutable_text` and `retrieval_status`. Qwen receives
the original structured rules and references without the fetched verse text.
The final response attaches trusted text separately from the generated result.
Missing text is never reconstructed by the model: failed retrieval leaves the
rule and reference intact with `retrieval_status: "unavailable"`.

Verses are cached as `data/sources/quran_cache/4_12.json` with retrieval timestamps
and checksums. Runtime cache files are ignored by Git; only the folder README is
tracked. No new rule selection or reasoning depends on remote text retrieval.

`shares[].fraction` is the group share of the whole estate. The authoritative
input is `post_tasil.distribution[].per_head_shares`, the share for one person.
Python replaces model-generated group shares, normalizes fractions, calculates
percentages, and checks that the count-weighted total equals one.

The local source set contains 14 structured records citing Quran 4:11, 4:12 and
4:176: spouses, daughters, joint sons/daughters, parents' specified fractions,
and full sisters or joint full siblings in the configured kalalah context.
Records are validated at load time. Threshold conditions use generic `_gte`
and `_lte` suffixes, alongside equality and integer comparison objects.

Kalalah context is conservatively defined for this batch as no descendant and
no father. This is a configured applicability feature, not a complete legal
determination. Parent fractions are partial rules: no father's residue is
encoded, and the mother's third record retains the verse's parental context
in its text. These records are not a complete rule system for compound cases.
No brother-alone, blocking, awl, radd, or extended-relative rules are added.
Coverage and arithmetic consistency do not establish legal completeness.

Normal model execution uses `think=False` and `temperature=0`. Optional reasoner
debug streaming remains available. The reasoner module returns model JSON;
verification runs separately in the pipeline. Its CLI still writes verified
output to `qwen_output.json`.

## First Fiqh RAG layer

The approved source is the Kuwaiti Fiqh Encyclopedia, published by Kuwait's
Ministry of Awqaf and Islamic Affairs. Approved source files must be supplied locally. Place approved local files in
`data/fiqh/kuwaiti_encyclopedia/raw/`; supported formats are UTF-8 TXT, Markdown, JSON and DOCX. See [the corpus guide](data/fiqh/kuwaiti_encyclopedia/README.md) for
required provenance and sidecar formats. Religious text is never fabricated,
paraphrased or automatically downloaded by ingestion.

Install the optional embedding runtime when a real corpus is ready:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-fiqh.txt
```

The local embedding model defaults to `BAAI/bge-m3` with 1024 dense dimensions.
Its first load may download the model weights from Hugging Face; prepare the
weights in advance for offline operation. The embedding model is independent
of Qwen. Qdrant is accessed through its REST API using the existing `requests`
dependency; no in-memory production store is substituted.

Run a Qdrant server separately. Set these shell environment variables as needed
(the project does not automatically read `.env`):

```text
QDRANT_HOST=http://localhost:6333
FIQH_COLLECTION=mawarith_fiqh
FIQH_EMBEDDING_MODEL=BAAI/bge-m3
```

Ingest, index, retrieve, and optionally check Qdrant connectivity:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.loader
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.vector_store
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.retriever
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.vector_store --check-connection
```

Retrieval prompts once with `السؤال:`. Python callers can use
`retrieve_fiqh(query, top_k=5, filters={"topic": "..."})`, with filters for
topic, source_name, section and volume. Results preserve exact text and metadata.
Results also return `previous_chunk` and `next_chunk` as exact source excerpts
from the same document, or null at document boundaries. Tiny fragments are
merged before indexing; actual DOCX article-title styles supply section metadata.
No missing legal headings or page numbers are guessed.

Run all three real quality queries with
`python -X utf8 -m backend.rag.fiqh.quality_check`; exact main text, neighboring
context and metadata are printed and saved in the ignored processed directory.
The main response separates `fiqh_evidence` from generated `result` and reports
`fiqh_retrieval.status` as `available`, `empty`, or `unavailable`.

Empty corpus retrieval is safe and returns no evidence without Qdrant or model
initialization. A nonempty corpus requires a working Qdrant collection and
embedding runtime; failures are explicit. RAG evidence **does not independently
determine inheritance rulings** and never increases structured source coverage.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend tests
```

## DOCX ingestion

Install `python-docx` from `requirements-fiqh.txt`. Place the Word document in
`data/fiqh/kuwaiti_encyclopedia/raw/` with a sidecar named exactly
`<filename>.docx.metadata.json`. Both the source URL and approved publisher
metadata must pass validation; no missing provenance is guessed.

```powershell
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.loader
```

This ingests supported files from the raw folder, including
`kuwaiti_fiqh_encyclopedia_vol_03.docx`. Body paragraphs are extracted in order
using python-docx. Only empty-string paragraphs are skipped. Whitespace,
Arabic diacritics, tabs and extracted line breaks are retained, and paragraphs
are joined with two newlines for conservative chunking. No source text is
rewritten. Table-cell paragraphs, including nested tables and merged cells, are extracted
once in document order. Headers and footnotes remain outside body extraction. Legacy `.doc` and PDF are not supported.
