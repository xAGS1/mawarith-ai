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

## Case clarification and v1 limitations

Case mode uses only `ready`, `needs_clarification`, `specialist_referral` and
`out_of_scope`. Learn mode is unchanged. Missing sibling subtype (full, paternal
or maternal), uncertain family facts, unspecified children or explicitly unlisted
relatives produce a localized `clarification_question` and no calculation.
For example, `ترك بنتًا وأخًا` asks whether the brother is full, paternal or maternal.
Clarifying a relation does not guarantee that its rules are covered by v1.

Advanced circumstances such as pregnancy, missing persons, successive deaths,
bequests or divorce return a specialist referral. So do cases outside structured
coverage, father/daughter cases needing an additional residue rule, and cases
whose retrieved fixed fractions require awl/radd or an uncovered residue rule.
The deterministic check stops the reasoner and verifier for these cases; it
does not supply any new inheritance rule or distribution. Trusted sources and
short explanations of retrieved rules remain available when found.

`/analyze-case` and the Qwen CLI also use these four states; the former
`insufficient_sources` state is now `specialist_referral`. Supported cases still
use the existing reasoner and Python fraction verifier. The clarification checks
recognize common explicit ambiguities; they are not a complete family intake.

## Advisory AI understanding and explanations

`POST /ask` retains its explicit `learn` / `case` mode. A strict Qwen classifier
now enriches the request with intent, language, explanation depth, question kind,
explicit deceased gender, an attached educational question, and proposed ambiguities.
Connection failures, timeouts or invalid classifier JSON use deterministic fallback.
Classification never overrides the supplied mode or deterministic case readiness.

Learn explanations receive backend-owned passage/claim associations and requested
depth; the existing citation and concept-scope checks remain in force. Verified
curated definitions and comparisons still bypass generated redefinition.
For a ready mixed case, Qwen selects/orders relevant confirmed rule claims. Python
renders their factual wording unchanged, so this layer cannot edit distributions
or introduce rulings. English mixed-case explanations currently retain the original
Arabic rule wording with an English label, rather than invent a rule translation.
Unsupported attached questions receive a limitation, without changing case readiness.

For internal demos, call `run_request(question, mode, debug_trace=trace)` with an
empty dict. It receives intent, entities from the existing relation parser,
ambiguity proposals, deterministic readiness confirmation, selected rule/source
IDs and evidence plans. No chain-of-thought is requested or stored. This argument
is not exposed by the HTTP schema and traces do not enter normal API responses.
Trace dictionaries include case/source data; store them only if needed for debugging.

The existing calculation path is unchanged: Qwen proposes a rule-backed
distribution, and Python verifies its fraction arithmetic. This change does not
introduce a deterministic allocation engine or claim that arithmetic consistency
alone proves a distribution's religious correctness.

## Source-traceable curated learning content

The curated learning schema separates `definition` (`text`, `status`, `source_id`,
`reviewer`, `reviewed_at`), `properties` (the same metadata with `value`), and
`source_records` (approved provenance and unchanged `exact_text`). Content statuses
are `source_verbatim`, `reviewed_summary`, or `draft`. Verbatim values must be exact
substrings of their approved passage; reviewed summaries require a reviewer and
review date. Draft values cannot enter verified definition or comparison output.

Only `fixed_share` and `residuary_heirs` are migrated. Their existing bilingual
summary drafts are preserved internally in `educational_summaries`; no reviewer
identity/date was available and none was invented. Verified definitions/properties
currently use the approved Arabic passage. English output labels those passages
in English while retaining their exact Arabic wording, pending reviewed translations.

Populated properties are `share_type`, `has_fixed_fraction`, `examples_of_fraction`
for fixed shares, and `share_type`, `may_receive_whole_estate`,
`may_receive_remainder`, `may_receive_nothing` for residuary heirs. Verbatim
properties hold exact passage text (or exact fraction terms), not inferred Boolean
flags. Residuary outcome properties retain the complete conditional passage.
No eligibility rules, additional recipient categories or opposite outcomes were
inferred. Other curated concepts remain unverified and empty.

The generic comparison renderer intersects verified property keys and preserves
each property's source mapping. It renders source text and reviewed summaries
with distinct labels, never uses a draft, and falls back to the existing grounded
flow when either concept or shared properties lack support. Source excerpts always
contain source wording, never reviewed summaries or generated AI explanation.
