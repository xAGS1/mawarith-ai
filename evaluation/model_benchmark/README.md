# Isolated MAWARITH AI model benchmark

This benchmark calls Ollama directly and **does not change the MAWARITH production
model**, environment, provider, pipelines, frontend or application configuration.
It imports no backend modules and needs only Python's standard library.

Start Ollama, then download both models:

```powershell
ollama pull qwen3:8b
ollama pull qwen3:14b
```

Run from the project root:

```powershell
python evaluation/model_benchmark/compare_models.py
```

The default host is `http://127.0.0.1:11434`. Optional flags are `--host`,
`--timeout` (default 600 seconds per request) and `--max-output-tokens` (default 512).
Both models receive identical system/user prompts, temperature 0, context size
4096, output limits, `think=False`, and non-streaming requests. Each request
unloads its model afterward; reported end-to-end latency includes model loading.

Only the four questions are supplied: no approved source passages or inheritance
rules are included. This measures raw instruction-following, ambiguity handling
and abstention under that constraint; it is not a sourced solver evaluation or
proof of religious accuracy. No chain-of-thought is requested or recorded.

Timestamped UTF-8 JSON reports are saved in `results/`, with a compact terminal
summary. Each report records settings, exact prompts, answers, latency and errors.
Completed records are saved after every request. Model-loading/resource failures
are recorded without stopping the remaining requests. Qwen3-8B runs first, so a
larger-model RAM/VRAM failure cannot prevent its results from being collected.

Manual scoring fields (`parsing_correct`, `factual_error`, `correct_abstention`,
`explanation_quality`, `notes`) are intentionally empty. No model auto-scores
responses. Exit status is 0 when all requests succeed, 1 when any fail, or 130
when interrupted. This script never downloads models or changes their setup.

## Two benchmark modes

Raw benchmark (question-only abstention and instruction following):

```powershell
python evaluation/model_benchmark/compare_models.py
```

Grounded benchmark (frozen-evidence explanation quality, Qwen3-8B vs Qwen3-14B):

```powershell
ollama pull qwen3:8b
ollama pull qwen3:14b
python evaluation/model_benchmark/grounded_compare_models.py
```

The grounded script is independent of the raw script and imports no application
modules. It reads only `grounded_questions.json`, calls Ollama directly, and writes
`results/grounded_benchmark_<UTC timestamp>.json`. It never calls live RAG, Qdrant,
the solver or source adapters, nor reads production configuration. Both models
receive the same prebuilt prompts, ordered evidence, temperature 0, `think=false`,
`num_ctx=4096`, `num_predict=512`, `stream=false` and `keep_alive=0`. The same CLI
flags supported by the raw runner can override host, timeout and output limit.

### Frozen evidence

- **q1 — أصحاب الفروض:** no evidence is supplied. The current curated catalog has
  no verified general definition; a narrower subtype or fixed-fraction list is
  not substituted. Abstention is an appropriate outcome.
- **q2 — الفرض والتعصيب:** exact approved Kuwaiti Fiqh Encyclopedia volume 3
  paragraphs used by the curated `fixed_share` and `residuary_heirs` comparison.
  The first enumerates prescribed fractions; the second preserves the whole-estate,
  remainder and no-remainder outcomes together. The frozen file includes original
  chunk IDs, exact offsets, source URLs, provenance and text hashes.
- **q3 — wife, mother, two sons and daughter:** trusted cached QuranEnc Arabic
  Quran 4:11 and 4:12, plus the existing `wife_with_descendant`, `mother_with_child`
  and `sons_and_daughters` structured rule summaries. Summaries are explicitly
  labelled separately from verbatim source passages. No calculated distribution
  or hidden case facts are supplied.
- **q4 — daughter and unspecified brother:** trusted cached Quran 4:11 and the
  existing `one_daughter_without_son` rule summary only. No brother subtype,
  assumed sibling rule or final distribution is supplied.

These excerpts were frozen from local approved processed chunks, existing
`data/sources/inheritance_rules.json`, and cached trusted Quran source records.
Runtime does not reread those files or choose evidence differently per model.
Exact source text is unchanged. Excerpt hashes are validated before any request;
the report stores the frozen-file hash, exact prompts, prompt hashes and evidence
for reproducibility. Text-hash checks detect changes; they do not independently
establish religious accuracy or approval. The full question/source mapping is in
`grounded_questions.json`.

The focus is evidence-grounded explanation and ambiguity handling, **not solver
accuracy**. Manually inspect reversed conditions and unsupported additions. Empty
scoring fields are `grounded_correctly`, `factual_error`, `added_unsupported_claim`,
`reversed_condition_error`, `correct_abstention`, `ambiguity_handled`,
`explanation_quality` and `notes`. No model auto-scores answers. Request failures
are recorded and remaining requests continue; latency includes loading. Neither
benchmark changes MAWARITH's production model or runtime behavior.
