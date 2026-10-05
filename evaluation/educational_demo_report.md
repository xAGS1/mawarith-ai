# Educational demo reliability pass

## Scope and implementation

The understanding → multi-source retrieval → Qwen explanation flow is preserved.
Retrieval, source ingestion, model/configuration, Quran adapter, solver,
executable inheritance rules, request understanding and frontend were untouched.

Educational generation now explicitly prefers precision over completeness:
short evidence produces a short answer, examples cannot become universal rules,
and conditions, exceptions, negations and school qualifications must survive.
The prompt prohibits model-memory elaboration and invented classifications.

An internal generation format requests at most three short statements with
individual evidence citations. The provider joins these into the existing
`answer` and `evidence_ids` fields. The public response schema is unchanged.
The calculation prompt and its internal output schema are unchanged.

A small deterministic sentence screen aligns each statement to short passages
in its cited evidence. Arabic spelling/layout normalization and bounded lexical
similarity allow close paraphrases; words from unrelated paragraphs cannot be
combined to justify a new statement. Negation and explicit conditional markers
are checked. Uncertain sentences are removed individually, before the existing
claim guard. If none remain, the existing insufficiency response is used.

The screen is deliberately conservative: at least 75% of content words must
align, with at most one unmatched word. It is a lexical safety screen, **not a
general semantic entailment proof**. Distant faithful paraphrases may be omitted;
subtle unsupported claims using the same vocabulary may still evade it.
No LLM grades its own answer. No concept mappings, routing patterns, religious
rules, hierarchy parsers or per-concept validators were added.

One generic consistency check removes explicit count/list mismatches and
contradictory same-subject fractions. Different conditional allocations are not
treated as contradictions. No regeneration loop or additional model request
was added to answering.

## Validation

- Sentence and orchestration regressions are included in the passing full suite.
- Full backend suite, including existing case/solver regressions: **500 passed**.
- Python compilation checks passed.
- Tests preserve short natural paraphrases, remove extra clauses independently,
  reject missing evidence, prevent cross-paragraph word borrowing, preserve
  negation/conditions, detect count and fraction contradictions, and confirm
  the calculation prompt remains unchanged.

Reproduce:

```powershell
python evaluation/check_educational_demo.py
python evaluation/check_educational_demo.py --recheck
python -m pytest -q -p no:cacheprovider --tb=short
```

Full source-bearing production transcripts and removed-sentence reasons remain
git-ignored in `data/fiqh/dorar_inheritance/processed/educational_demo.json`.
The live run uses the actual current local Qwen and approved multi-source RAG.

## Files changed in this pass

- `backend/llm/qwen_explainer.py`: educational-only prompt and internal format.
- `backend/pipeline/rag_answer.py`: apply educational sentence checks.
- `backend/pipeline/educational_sentence_check.py`: new generic text screen.
- `tests/test_educational_sentence_check.py`: new focused regressions.
- `tests/test_llm_first_rag.py`: orchestration fixture now contains evidence for
  its mocked explanation instead of an unrelated placeholder passage.
- `evaluation/check_educational_demo.py`: ten live questions.
- `evaluation/educational_demo_report.md`: this report.

Other worktree changes predate this pass.

## Ten-question production check

All ten questions were run through live production understanding, real local
multi-source retrieval and Qwen with the final educational prompt. After fixing
generic definition boundaries and a connective-normalization bug, the saved
**actual live generations** were replayed through the production educational
post-processing path and current real retrieval. Rechecking does not regenerate
answers or ask an LLM to judge them; it reuses the recorded model output.
The artifact explicitly marks `postcheck_replayed` and preserves generation
token metrics. No unit-test source fixtures were used for this audit.

| Question | Final presentation | Review |
| --- | --- | --- |
| ما معنى أصحاب الفروض؟ | Abstains | Removes count-based elaboration and an unsupported reconstructed definition; source gap remains |
| ما معنى العصبة؟ | Short definition retained | Removes the invented two-part classification that listed three items |
| ما الفرق بين الفرض والتعصيب؟ | Two short definition statements | Removes no supported statement; no additional entitlement conditions are invented |
| ما معنى الحجب؟ | Language meaning and concise technical definition | Both deprivation and reduced entitlement remain in the definition |
| ايش هي العول؟ | Short definition retained | Omits unsupported proportional elaboration |
| ما معنى الرد؟ | Language meaning and bounded technical definition | No-residuary qualification retained; model output has a minor spelling error in حقوقهم |
| فهمني العصبة ببساطة | Abstains | Removes المورثون, invented classification and an unsupported extra allocation statement |
| ليش يصير العول؟ | Short supported increase explanation | Omits doubtful proportional elaboration; answer remains limited |
| كيف الحجب يأثر على الورثة؟ | Abstains | Removes unsupported and unclear generated statements |
| وش يعني الرد؟ | Short supported explanation retained | No added classifications or fractions |

**7 retained answers; 3 safe abstentions.** These results improve the observed
demo behavior but do not establish complete semantic validation. The conservative
screen can still omit valid distant paraphrases, including translations whose
wording does not align with the evidence. Manual review remains relevant.

Observed concise examples:

- العصبة: «العصبة تعني الإرث بغير تقدير.»
- العول: «العول هو زيادة في الفروض تؤدي إلى زيادة في أصل المسألة.»
- الرد, conversational variant: «الرد هو بقاء مال من التركة بعد قسمتها.»

Full answers, exact separately retained excerpts, source citations and removed
sentences are available in the ignored local audit JSON, not redistributed here.
