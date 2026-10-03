# mawarith-ai
MAWARITH AI is an Arabic-first intelligent Islamic inheritance reasoning system with structured heir parsing, source-grounded fiqh retrieval, deterministic verification, and explainable inheritance calculations.

## Current pipeline

```text
Question -> Qwen relation parser -> Shared factual case features
         -> Shared condition-aware local rule retriever -> Shared source coverage gate
         -> Qwen reasoner only when coverage is sufficient
         -> Shared Python fraction verifier -> Final JSON with sources
```

With Ollama running and `qwen3:8b` installed, run from the project root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m backend.pipeline.qwen_pipeline
```

Output includes `question`, `parsed_relations`, `case_features`, `sources`,
`source_coverage`, `decision_state` and `result`. When any mentioned relation has
no retrieved rule in `applies_to`, Python returns `insufficient_sources` with
`result: null` and skips both reasoning and verification. Otherwise the state is
`ready` and reasoning runs followed by verification. An empty parsed case is blocked.

The CLI currently demonstrates the wife/full-brother case, which should be blocked
because the source library has no rule for the brother. Coverage measures distinct
relation names, not head counts, and checks availability rather than legal completeness.
The model-independent modules under `backend/rules/`, `backend/rag/`,
`backend/verifier/` and `backend/schemas/` do not import Qwen.

`shares[].fraction` is the group share of the whole estate. The authoritative
input is `post_tasil.distribution[].per_head_shares`, the share for one person.
Python replaces model-generated group shares, normalizes fractions, calculates
percentages, and checks that the count-weighted total equals one.

The local source set contains four rules from Quran 4:11 and 4:12, including
the wife's 1/8 with descendants and 1/4 without descendants. It does not cover
general inheritance cases or a brother's share. Arithmetic consistency does
not establish the legal correctness of a ruling.

Normal model execution uses `think=False` and `temperature=0`. Optional reasoner
debug streaming remains available. The reasoner module returns model JSON;
verification runs separately in the pipeline. Its CLI still writes verified
output to `qwen_output.json`.

Run checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q backend tests
```
