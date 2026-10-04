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


## Educational backend

`POST /ask` accepts `{"mode":"learn","question":"What is a fixed-share heir?"}`.
The explicit modes are `learn` (default) and `case`. The existing `/analyze-case`
solver remains compatible. Run the educational CLI with:

```powershell
python -X utf8 -m backend.pipeline.learn_pipeline
```

The CLI prompts once with `السؤال:` and accepts Arabic or English. It uses the
existing local Qwen/Ollama, BGE-M3 and Qdrant configuration; no new model or index
is required. `source_excerpts` contains exact approved source records and their
neighbors, independently of the generated `answer` and `key_concepts`. Quran
text comes exclusively from the source adapter after reasoning; only references
actually present in evidence and the existing rule library are enriched.

No matching evidence, retrieval failure, invalid evidence IDs, or an unsupported
explanation returns `specialist_referral`. Empty questions request clarification.
Case mode preserves structured-rule coverage and fraction verification; unsupported
cases return no distribution. `case_details` preserves the solver diagnostics.
The source library is limited, volume 3 contains multiple topics, and page numbers
are unavailable. A retrieved match and valid evidence IDs do not prove semantic
support for every generated claim. Explanations are educational, not complete
legal determinations. No new rules or source content were added.

Learn-mode evidence uses backend-assigned `E1`, `E2`, etc. Generated explanations
cite these IDs inline; unknown IDs or answers without support are withheld.
Source metadata is never generated by Qwen. Retrieval uses three main hits and
at most one adjacent excerpt, with overlapping text removed through immutable
document offsets and a 5,000-character source budget. Short concept queries get
inheritance context; when approved metadata identifies one inheritance article,
the existing section filter restricts retrieval to it. Comparisons split the
three-hit budget between their two concepts. Source text remains exact.

Qwen uses `think=False`, temperature 0, an 8,192-token context and a maximum of
450 output tokens. The connection/read timeouts are 10/240 seconds. On timeout,
the pipeline uses a minimal deterministic answer only when source-bound concept
metadata matches the retrieved passages and covers the requested concepts;
otherwise it abstains. The small terminology catalogue covers fixed shares and
residuary inheritance using the existing approved passages, not new distribution
rules or source documents. English answers can cite Arabic evidence;
the returned Arabic excerpts remain unchanged.

## Concept cards, beginner path and examples

Read-only educational catalogs are available at:

- `GET /learn/concepts` and `GET /learn/concepts/{concept_id}`
- `GET /learn/paths` and `GET /learn/paths/{path_id}`
- `GET /learn/examples` and `GET /learn/examples/{example_id}`

The seven concept cards include Arabic/English titles, bilingual `short_definition`
and `learn_question`, difficulty, related concepts and availability. Definitions
reuse existing source-bound metadata only when its anchors match validated local
evidence. Otherwise `availability` is `limited`, `short_definition` is null, and
no definition is guessed. Blocking, awl, radd and fixed-share heirs currently lack
their own source-bound catalog definition and remain limited. A limited card can
still supply a question to `/ask`; the existing evidence and citation checks apply.

The `inheritance_beginner` path has seven static steps and no progress tracking.
Each step provides a bilingual question and `mode` for the existing `/ask` route.
Three curated examples combine sons and daughters with a wife and/or mother;
`case_supported` is checked against current structured-rule coverage. It indicates
coverage of the curated relatives, not a precomputed or guaranteed model result.
Examples contain no calculated shares.

To explore an example, fetch it, then submit its `scenario_ar` or `scenario_en` to
`POST /ask` with `mode="case"`. For a detailed educational explanation or follow-up,
submit a question to the same endpoint with `mode="learn"`. The existing pipelines
perform parsing, retrieval, generation and verification; catalogs invoke no model.
