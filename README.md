# MAWARITH AI

Arabic-first Islamic inheritance education, grounded in source evidence, with deterministic calculation for supported cases.

MAWARITH separates language understanding and explanation from inheritance rule selection and arithmetic. The AI explains supplied evidence and verified results; it does not determine final shares. Ambiguous cases ask for clarification, and unsupported cases stop with a specialist referral.

## Current experience

- Arabic/English interface with RTL/LTR support.
- Educational questions, definitions, comparisons and contextual tutors.
- Seven concept lessons, four learning paths and four calculation learning paths.
- Natural-language case extraction followed by deterministic readiness checks and calculation.
- Requests owned independently by the homepage, concept and path surfaces. Pending requests survive client-side navigation; completed answers, drafts and meaningful errors are restored from session storage.
- Local duplicate-submit protection, cancellation and retry. Backend generation capacity is limited to two concurrent requests per process; waiting generation calls queue.
- Compact answers, exact source excerpts behind disclosures, and separate applied-rule details.
- Source-summary chips deduplicated by source name and reference. Book chips summarize volume; detailed metadata retains page locations and links.
- Clarification-only language validation and Arabic/English fallbacks. Empty or duplicate educational explanations are hidden in clarification cards.
- Deterministic referral explanations where the reason is known, with a generic fallback for unknown reasons.

## Architecture

```text
User question
    → structured language/intent understanding
    ├─ education → multi-source retrieval → selected evidence
    │              → AI explanation → provider-specific sentence checks
    │              → grounding/claim checks → answer and sources
    └─ calculation → normalized relatives and presence features
                     → readiness and eligibility checks
                     → fixed shares → supported residuary family
                     → exact verification → explanation and rule trace
```

The primary provider configured in [.env.example](.env.example) is **Fanar-C-2-27B**. An optional **Ollama/Qwen3-8B** transport remains available. Without `LLM_PROVIDER`, the transport defaults to Ollama; use an explicit setting when starting the application.

Fanar receives MAWARITH-selected evidence. Fanar-Sadiq or external Fanar retrieval is not used. Provider fallback is disabled by default and must be explicitly enabled.

Educational safety is provider-specific:

- Actual Fanar generations bypass the strict lexical/near-verbatim support gate, while retaining the existing hard checks and claim/grounding safeguards.
- Ollama/Qwen generations retain stricter sentence support checks. Explicit Fanar-to-Ollama fallback uses the actual generation provider's policy.
- These checks detect bounded classes of errors; they are not a general semantic entailment proof. An answer can be shortened or withheld when support is insufficient.

Retrieval never grants a new executable inheritance rule. Arithmetic consistency does not establish complete fiqh correctness.

## Deterministic calculation scope

Legal shares use `fractions.Fraction`. Percentages are display values, not inputs to legal arithmetic.

The direct-children residuary family supports arbitrary positive counts within validated inputs:

- Sons only: divide the actual residue equally.
- Sons and daughters: divide the actual residue with weights 2:1.
- Daughters without sons: retain existing fixed-share rules; they are not routed through the children residuary family.
- Supported spouse/parent fixed shares are assigned before distributing the residue. The family does not assume the entire estate remains.

Examples covered by deterministic regressions:

| Case | Per-person shares |
| --- | --- |
| One son | Son: 1 |
| Two sons | Each son: 1/2 |
| Three sons | Each son: 1/3 |
| Son and daughter | Son: 2/3; daughter: 1/3 |
| Two sons and two daughters | Each son: 1/3; each daughter: 1/6 |
| Wife and two sons | Wife: 1/8; each son: 7/16 |
| Wife, son and daughter | Wife: 1/8; son: 7/12; daughter: 7/24 |

These examples describe the supported, fully stated test cases. Additional relatives or circumstances require another readiness and coverage check.

Presence is computed before exclusion. A person receiving no share is not automatically treated as absent from all case features. The implemented son-to-agnatic-grandson exclusion preserves presence and records a zero share. Other undefined exclusion policies remain referrals.

Descendants through sons are distinguished from descendants through daughters. Daughter-line descendants do not incorrectly activate the inheriting-descendant feature; their calculation remains unsupported.

Named guards include `unsupported_umariyyat`, `unsupported_matrilineal_descendant`, `unsupported_sibling_exclusion_policy` and `unsupported_external_impediment_policy`. The Umariyyat guard prevents silently applying the ordinary mother-third rule; a full Umariyyat implementation is not provided.

Existing fixed-share and limited full-sibling rules remain available where coverage is complete. This is not a complete sibling, grandfather or distant-residuary system. Automatic awl/radd allocation is not implemented. Unsupported residue, competing families, ambiguous relationships and advanced circumstances continue to stop safely.

Solver results include `rule_trace` entries with rule/category IDs, affected heirs, exact fractions, input residue where relevant, and source IDs. Existing Quran rules remain in [inheritance_rules.json](data/sources/inheritance_rules.json); bounded local fiqh evidence for the new solver family is in [solver_sources.json](backend/rules/solver_sources.json).

For example, a wife-only case identifies her supported fixed share but refers because the remainder-allocation policy is unsupported. The backend explains this limitation without displaying a final distribution or asking an LLM to infer the reason.

## Sources and retrieval

The educational retrieval code combines local evidence from:

- Kuwaiti Fiqh Encyclopedia.
- Umm Al-Qura University Mawarith course.
- Dorar Fiqh Encyclopedia, inheritance book only.
- Approved locally cached Quran passages resolved through the exact-text adapter.

BGE-M3 supplies embeddings and Qdrant supplies vector retrieval. Local source candidates also participate in educational retrieval; the source pool depends on installed, approved local material. Do not assume a fresh checkout has the full demonstration corpus.

Exact source text remains separate from reviewed summaries and generated explanation. A retrieved example does not authorize a universal rule. Source excerpts, qualifications, metadata and citations must remain traceable to their evidence.

Raw source files, downloaded HTML snapshots and processed full corpora under `data/fiqh/` are git-ignored. Obtain and approve source material locally before ingestion. Inclusion in the application does not establish redistribution rights. Do not publish the full corpus or infer license approval from source availability.

## API

The browser calls Next.js `/api/ask`, which proxies to FastAPI using `BACKEND_API_URL`.

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Process health response |
| `POST /ask` | Educational/case orchestration and presentation |
| `POST /analyze-case` | Structured deterministic case result |
| `GET /learn/concepts`, `/learn/paths`, `/learn/examples` | Read-only learning catalogs; each also has an identifier route |
| `GET /docs` | FastAPI interactive API documentation |

Example `/ask` payloads:

```json
{"mode":"learn","question":"ما معنى العصبة؟"}
```

```json
{"mode":"case","question":"مات وترك زوجة وابنين"}
```

`mode` preserves the legacy request interface. In the current semantic path, understanding determines the actual educational/calculation intent; the mode acts as a compatibility hint for fallback behavior. It is not a guarantee that contradictory question text will be forced into that mode.

Contextual tutors may supply optional `concept_context` with bounded `slug` and `title` strings. Context is a retrieval/understanding hint, not evidence or an answer. Calculation does not use educational page context to change shares.

Responses retain `mode`, `language`, `decision_state`, `answer`, `clarification_question`, `sources`, `source_excerpts`, `limitations` and optional `case_details`. Educational responses also use `evidence_status`.

| Decision state | Meaning |
| --- | --- |
| `ready` | Supported educational answer or supported, verified calculation |
| `needs_clarification` | Missing or ambiguous information requires a user response |
| `specialist_referral` | Calculation cannot safely produce a final distribution |
| `out_of_scope` | Request is outside the current scope |

Educational evidence insufficiency is presented as “تعذر تقديم شرح موثق”, rather than case-referral wording. Public responses omit private retrieval diagnostics and local source paths. Structured solver rule traces are distinct from hidden model reasoning.

## Local setup

Run backend commands from the repository root. You need Python, Node.js/npm, a Fanar API key or local Ollama, and Qdrant plus approved local evidence for vector-backed retrieval.

### Python and retrieval dependencies

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pip install -r requirements-fiqh.txt
Copy-Item .env.example .env
```

`requirements-fiqh.txt` contains the optional BGE-M3 embedding and DOCX dependencies. Qdrant is accessed through its REST API. The first embedding-model load may require downloading model files; subsequent use can use the local cache.

### Provider configuration

Set values in the root `.env`:

```dotenv
LLM_PROVIDER=fanar
FANAR_API_KEY=your_key_here
FANAR_BASE_URL=https://api.fanar.qa/v1
FANAR_MODEL=Fanar-C-2-27B
LLM_FALLBACK_PROVIDER=none
QDRANT_HOST=http://localhost:6333
FIQH_COLLECTION=mawarith_fiqh
FIQH_EMBEDDING_MODEL=BAAI/bge-m3
FIQH_EMBEDDING_BATCH_SIZE=32
```

FastAPI loads the root `.env` at startup without overriding existing process environment values. Restart the backend after configuration changes. Standalone scripts do not necessarily perform the same startup loading; check their entry point before assuming they use `.env`.

For a local primary provider, set `LLM_PROVIDER=ollama`, `OLLAMA_HOST=http://127.0.0.1:11434` and `OLLAMA_MODEL=qwen3:8b`, then prepare Ollama:

```powershell
ollama pull qwen3:8b
ollama serve
```

Start `ollama serve` only if the local service is not already running. To enable local fallback from Fanar, keep Fanar as primary and explicitly set `LLM_FALLBACK_PROVIDER=ollama`.

### Qdrant and local corpus

Use an existing Qdrant instance at `QDRANT_HOST`. An optional local Docker instance can be started with persistent named-volume storage:

```powershell
docker run -d --name mawarith-qdrant -p 6333:6333 -v mawarith-qdrant-data:/qdrant/storage qdrant/qdrant
```

Check connectivity without indexing:

```powershell
python -m backend.rag.fiqh.vector_store --check-connection
```

Source preparation is explicit, not an application-startup step. Source-specific tools include `backend.rag.rebuild_uqu`, `backend.rag.dorar_ingestion` and the fiqh ingestion/indexing modules. Inspect their `--help` and local metadata before running them. Do not rebuild or replace an existing collection merely to start the app.

### Start FastAPI

```powershell
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

API documentation: <http://127.0.0.1:8000/docs>. `/health` confirms the server is running; it does not certify provider credentials or corpus readiness.

### Start Next.js

In a separate terminal:

```powershell
cd frontend
npm.cmd ci
Copy-Item .env.example .env.local
npm.cmd run dev
```

The frontend `.env.local` should contain `BACKEND_API_URL=http://127.0.0.1:8000`. Open <http://localhost:3000>. Fanar credentials remain on the backend and must not be placed in frontend environment variables. On non-Windows systems use `npm` instead of `npm.cmd`.

## Validation

Backend unit/regression tests use mocked transports. Explicitly selecting Ollama for the test process avoids local Fanar settings interfering with older transport mocks; this does not change production configuration.

```powershell
$env:LLM_PROVIDER = 'ollama'
python -X utf8 -m pytest tests -q -p no:cacheprovider --tb=short
python -X utf8 -m compileall -q backend tests
Remove-Item Env:LLM_PROVIDER
```

If you already had an explicit provider in that shell, restore it instead of removing it. Do not start a production backend from the test shell while its test-only provider override is active.

Frontend:

```powershell
cd frontend
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

There is no `npm test` script. Playwright uses the production build by default, starts a fixture backend on port 3101 and Next.js on port 3100, and runs desktop/mobile projects. On Windows its default browser channel is Microsoft Edge; another installed channel can be selected through `PLAYWRIGHT_CHANNEL`. Tests use fixtures rather than spending live Fanar requests.

The suites cover exact children-family allocation and supported-domain properties, readiness/referral guards, source integrity, provider/fallback policies, clarification language, source-summary deduplication, session restoration and cross-page requests. Live-provider evaluations and retrieval benchmarks are separate checks, not substitutes for deterministic regression tests.

## Repository map

```text
backend/
  app.py              FastAPI entry point
  llm/                Provider transports and generation capacity
  parsing/            Structured relation extraction
  pipeline/           Educational/case orchestration and explanation checks
  rules/              Features, readiness, eligibility and exact allocation
  rag/                Educational evidence retrieval and source preparation
  learning/           Curated evidence and learning catalogs
  schemas/            API/result models
  sources/            Exact-source adapters
  verifier/           Fraction verification
frontend/
  src/app/            Homepage, lesson routes and API proxy
  src/components/     Tutors, answer presentation and learning UI
  src/lib/ask/        Requests, session state and presentation helpers
  tests/              Playwright regressions and fixture backend
data/                 Rule data, local source files and caches
tests/                Backend regressions
evaluation/           Benchmarks and historical validation artifacts
```

Evaluation reports describe their own run and may predate the current implementation. Use current source code and rerun commands above to assess present behavior; historical pass counts or successful model examples do not establish complete coverage.

## Limits and source policy

MAWARITH is an educational/research system with deliberately bounded calculation coverage. Pregnancy, missing persons, successive deaths, bequests, divorce-related circumstances, unsupported grandfather/sibling combinations, distant kindred and undefined juristic policies can require clarification or referral. A short question is not necessarily a supported calculation.

The project does not silently adopt disputed rules to complete a distribution. Missing coverage must be resolved through reviewed, source-traceable rule families. Retrieval relevance, model confidence and arithmetic equality alone cannot establish that coverage.

Keep API keys in environment variables and `.env` files out of Git. Session persistence is browser-session state, not a durable account history; avoid entering unnecessary personal information. Full corpora and private source-bearing audit artifacts must not be published automatically.

For real inheritance decisions, consult a qualified specialist who can review the complete facts and applicable religious/legal context.
