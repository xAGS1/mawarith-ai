# Seven-concept curriculum and contextual tutor

## Delivered experience

Seven pre-rendered routes use one bilingual curriculum component:

| Route | Static Arabic definition / content limit | Approved local source |
| --- | --- | --- |
| `/concepts/fixed-share-heirs` | لم يتوفر بعد تعريف مباشر وكامل معتمد لهذا المصطلح. | Kuwaiti Fiqh Encyclopedia, vol. 3, إرث. The available enumeration is shown only as a source excerpt, never as a complete definition. |
| `/concepts/fixed-share` | الفرض نصيب مقدر شرعًا لوارث مخصوص، لا يزيد إلا بالرد ولا ينقص إلا بالعول. | UQU Mawarith 1, PDF page 28, terminology appendix. |
| `/concepts/tasib` | التعصيب هو الإرث بغير تقدير. | UQU Mawarith 1, PDF page 13, التعصيب. |
| `/concepts/asabah` | العاصب هو من يرث بغير تقدير: إذا انفرد أخذ المال كله، وإذا كان معه صاحب فرض أخذ ما بقي بعده، فإن استغرقت الفروض التركة سقط. | UQU Mawarith 1, PDF page 28, terminology appendix. The whole/remainder/nothing qualifications are retained separately. |
| `/concepts/blocking` | الحجب منع شخص معين عن ميراثه كله أو بعضه بوجود شخص آخر، وفق التعريف المنقول عن صاحب السراجية. | Kuwaiti Fiqh Encyclopedia, vol. 3, إرث, attributed definition. |
| `/concepts/awl` | العول زيادة في الفروض ينتج عنها زيادة في أصل المسألة. | UQU Mawarith 1, PDF page 22, العول. |
| `/concepts/radd` | الرد صرف ما فضل عن فروض ذوي الفروض إليهم بقدر حقوقهم، ولا مستحق له من العصبات. | Dorar Fiqh Encyclopedia, inheritance book, تعريف الرد, page `https://dorar.net/feqhia/13751/`. The no-entitled-residuary qualification is retained. |

These are labeled source-based educational summaries. English uses faithful
translations of the same bounded summaries. Exact Arabic source text is kept
separately behind “عرض النص من المصدر”, with institution/publisher, section,
PDF page or volume and an external link where available. No UQU source URL was
invented. Short excerpt snapshots include document/chunk hashes and offsets;
they contain no local source paths or full corpora.

Only **Awl** has an example: the existing approved Kuwaiti Encyclopedia
wife/two-daughters/mother/father example, origin 24 increasing to 27. Its stated
shares and total are transcribed educationally; no new distribution is computed.
Other pages do not manufacture examples. The fixed-share-heirs page explicitly
states its evidence gap and does not invent a category diagram or definition.

Desktop: centered title/progress, cream educational panel on the right, compact
provenance on the left, gold-accent conceptual steps and a full-width optional
tutor below. Mobile stacks content, sources and tutor; the diagram becomes
vertical and input/submit remain touch sized. Existing navbar, footer and other
homepage sections retain their design. The seven homepage cards now navigate
to lessons instead of opening preview dialogs.

Browser screenshots (local, ignored test artifacts):

- `frontend/test-results/concept-awl-desktop.png`
- `frontend/test-results/concept-awl-mobile.png`

## Context adapter

The existing typed `ask()` helper accepts optional `{slug, title}` context.
Only contextual calls send `mode=learn` plus `concept_context`. Generic AskPanel
requests retain their existing inference and payload. The existing Next.js
`/api/ask` proxy already forwards JSON unchanged; it required no modification.

FastAPI validates the optional context with bounded strings and rejects unknown
context fields. Calculation requests ignore this context. Educational semantic
understanding receives it as separate untrusted page data, not a source or an
answer. The original user question remains intact. Retrieval keeps the original
question and model-selected query/concepts, adding only the current title as a
soft hint. No concept or source filter is imposed, and ranking is unchanged.
Generation receives the original question and context in a data envelope,
together with only the existing selected evidence. Sentence screening, scope
checks and the claim guard are unchanged. No second chatbot or RAG pipeline was
introduced. API response fields remain unchanged; only the optional request
field is new.

The tutor renders inline through the existing AskResult component, with compact
source chips and exact excerpts behind “عرض المصادر”. Empty input, loading,
duplicate blocking, errors, retry and insufficiency are covered. No request is
made merely by opening a lesson or selecting a suggested question.

## Production check and remaining limitation

`python evaluation/check_concept_tutor.py` ran actual local Qwen understanding,
production multi-source retrieval and existing safeguards, without fixtures.

- Awl page, “ليش أصل المسألة يزيد؟”: supported short answer:
  **العول هو زيادة سهام الفروض على أصل المسألة.** Sources: Dorar and UQU.
- Awl page, “طيب وش الفرق بينه وبين الرد؟”: understanding resolved both Awl
  and Radd; retrieval selected UQU pages 22/23 and Dorar definitions of both.
  Qwen generated an unsupported extra phrase in its Radd statement. Existing
  safeguards removed that statement and retained the supported Awl explanation,
  with the existing omitted-statements limitation. Thus contextual cross-concept
  retrieval works, but the live comparison answer was incomplete. No guard was
  weakened to make it appear complete.

Source-bearing debug output remains ignored:
`data/fiqh/dorar_inheritance/processed/concept_tutor_live.json`.
The live run used the existing cached embedding model; a blocked Hub metadata
check fell back to the local cache. No model, configuration or sources changed.

## Validation

- Frontend TypeScript: passed.
- Production Next.js build: passed, all seven concept routes generated as static HTML.
- Formatting check: passed. This repository has no configured ESLint/lint script;
  no new lint dependency was added or a formatting check mislabeled as lint.
- Full backend suite: **504 passed** (includes existing solver/case regressions).
- Focused educational/context suite: **37 passed**.
- Browser suite: **54 existing tests passed**, with 2 desktop-only checks skipped
  on mobile. **8 concept tests passed** on desktop/mobile after scoping alert
  selectors to avoid Next.js's hidden route announcer.
- Python compilation: passed.
- Screenshots manually inspected; no overflow or hydration errors observed.
- All static routes open without calling the backend; exact quotes remain collapsed.
- Raw/processed source corpora and the live audit JSON remain git-ignored.

## Exact files added/changed in this task

Frontend additions:

- `frontend/src/app/concepts/[slug]/page.tsx`
- `frontend/src/components/concepts/concept-lesson.tsx`
- `frontend/src/components/concepts/concept-tutor.tsx`
- `frontend/src/data/concept-curriculum.ts`
- `frontend/src/data/concept-evidence.json`
- `frontend/tests/concepts.spec.ts`

Frontend updates:

- `frontend/src/app/globals.css` — scoped curriculum styles and link/focus treatment.
- `frontend/src/components/home/concept-cards.tsx` — lesson navigation.
- `frontend/src/components/ask/ask-result.tsx` — optional compact source disclosure.
- `frontend/src/lib/ask/client.ts` — optional contextual educational payload.
- `frontend/src/lib/ask/types.ts` — context type.
- `frontend/tests/home.spec.ts` — updated concept navigation expectation.
- `frontend/tests/localization.spec.ts` — updated bilingual navigation expectation.

Minimal backend/API updates:

- `backend/app.py`
- `backend/llm/qwen_understanding.py`
- `backend/pipeline/semantic_request.py`
- `backend/pipeline/educational_pipeline.py`
- `backend/pipeline/rag_answer.py`

Tests and audit:

- `tests/test_concept_tutor.py`
- `evaluation/check_concept_tutor.py`
- `evaluation/concept_curriculum_report.md`

Solver, executable rules, model settings, source ingestion, Quran adapter,
claim-guard implementation and other homepage sections were untouched by this
task. Other existing worktree changes predate this implementation.
