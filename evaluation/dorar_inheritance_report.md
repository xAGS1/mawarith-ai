# Dorar inheritance HTML integration

Only the **كتاب المواريث** subtree is ingested. No OCR, PDF processing,
LLM source repair, executable rules or question-specific answers were added.

## Access, scope and counts

The cached [robots.txt](https://dorar.net/robots.txt) returned HTTP 200 and
`User-agent: * / Disallow:` on 2026-10-05. Requests use a descriptive
MAWARITH User-Agent, at least 1.05 seconds between requests, and immutable
local snapshots. A refusal, rate limit or scope-changing redirect stops the
crawl. Permission to crawl does not establish redistribution rights:
`license_status` remains `needs_review`.

Discovery starts with [the inheritance definition article](https://dorar.net/feqhia/13638)
and the site's navigation tree. The full navigation index is read for discovery
only; no articles from other books enter the corpus. Related links are followed
only when their titles map to the inheritance subtree.

- 77 inheritance URLs discovered and successfully downloaded/cached.
- 61 article pages; 16 navigation-only pages skipped; 0 failed downloads.
- 62 coherent topical chunks. Two oversized blocks are retained locally but
  excluded from retrieval rather than cutting their qualifications.
- **60 Dorar points** added to existing `mawarith_fiqh`.
- Existing Kuwaiti point IDs remain identical: **1,707**. Total collection:
  **1,767**. Existing `mawarith_uqu`: **47**, untouched.
- Eight pages contain image-only tables/figures. Their text is preserved and
  marked `has_unextracted_visual`; missing table values are not fabricated.

Skipped navigation IDs: 13642, 13652, 13643, 13662, 13669, 13674, 13687,
13718, 13729, 13743, 13732, 13764, 13763, 13779, 13784, 13787.
Oversized article IDs: 13681, 13705.

## Extraction, indexing and retrieval

`lxml` extracts only the article container. Headings, Arabic wording, quotation
text, footnote numbers and their bibliography are retained. HTML layout
whitespace is normalized; letters and source statements are never rewritten.
Related links, navigation, buttons and footer are excluded.

Named topical boundaries split chunks. Evidence, exceptions, conditions and
attributed school disagreement stay with their governing statement. Each chunk
has the requested hierarchy, URL, source/type, primary content kind, exact text,
document hash, excerpt hash and stable chunk ID. A primary `rule` or
`disagreement` block may include evidence subheadings; those are not detached.
No numeric PDF page is invented for HTML articles.

Indexing checks the existing vector configuration, upserts source-namespaced
IDs, verifies every replacement, then prunes stale **Dorar-only** IDs.
Retrieval verifies Qdrant text against the approved local snapshot hash.
The source is optional in shared UQU/Kuwaiti/Quran retrieval. Ranking adds small
content-kind, extraction-quality, source-type and punctuation-insensitive topic
preferences to semantic similarity. No concept-to-page answer table is used.
Public citations preserve source/title/publisher/topic/URL; hashes and internal
provenance remain internal, and local paths are not returned.

Reproduce from the repository root:

```powershell
python -m backend.rag.dorar_ingestion --index
python evaluation/check_dorar_live.py
python -m pytest -q -p no:cacheprovider --tb=short
```

Subsequent ingestion reuses cached HTML. Full snapshots, extracted corpus,
manifest, failed/skipped details and live traces are under the git-ignored
`data/fiqh/dorar_inheritance/{raw,processed}/` directories.

## Coverage audit

These are extraction observations, not new executable religious rules. A
heading, enumeration or consequence is not counted as a complete definition.
The exact short excerpts below omit no condition within the quoted sentence;
associated bibliography remains in the local source chunks.

| Concept | Direct Dorar definition | Best page / exact support | Qualifications and examples | Existing source comparison |
| --- | --- | --- | --- | --- |
| أصحاب الفروض | Not found | [Fixed-share chapter](https://dorar.net/feqhia/13688); definitions of الفرض and separate share-holder lists do not define the entire category | Lists have entitlement conditions; not promoted into a universal definition | UQU enumeration and Kuwaiti count/list do not close this definition gap |
| الفرض | Yes | [13688](https://dorar.net/feqhia/13688): «والفَرضُ: هو النَّصيبُ المُقدَّرُ شَرعًا لوارِثٍ خاصٍّ، لا يُزادُ إلَّا بالرَّدِّ، ولا يَنقُصُ إلَّا بالعَولِ» | Keeps both adjustment qualifications; six fractions occur in an associated footnote | Complements the UQU glossary and Kuwaiti fixed-fraction passage |
| العصبة | No complete direct definition found | [13702](https://dorar.net/feqhia/13702): «مِن أنواعِ الوارِثينَ: مَن يَرِثُ بالتَّعصيبِ.» | Supporting evidence and categories exist, but this introduction is not a definition | UQU has direct terminology; Kuwaiti has bounded inheritance-behavior evidence |
| التعصيب | Supporting explanation, not complete direct definition | [13702](https://dorar.net/feqhia/13702) contains attributed remainder explanation and supporting citations | Conditions and evidence retained together; no invented generalization | UQU's direct definition remains useful |
| الحجب | Yes | [13711](https://dorar.net/feqhia/13711): «واصطِلاحًا: مَنعُ مَن قامَ به سَبَبُ الإرثِ مِنَ الإرثِ بالكُلِّيَّةِ، أو مِن أوفَرِ حَظَّيه» | Both deprivation and reduction retained; further chapters give bounded examples | UQU and Kuwaiti definitions already exist; adds clean HTML and citations |
| العول | Yes | [13744](https://dorar.net/feqhia/13744): «واصطِلاحًا: هو زيادةُ سِهامِ الفُروضِ على أصلِ المَسألةِ» | [13746](https://dorar.net/feqhia/13746) has attributed ruling and example context; image table is not extracted | Complements UQU and Kuwaiti evidence |
| الرد | Yes | [13751](https://dorar.net/feqhia/13751): «واصطِلاحًا: صَرفُ ما فضَلَ عَن فُروضِ ذَوي الفُروضِ إليهم ولا مُستَحِقَّ له مِنَ العَصَباتِ بقَدرِ حُقوقِهم» | [13753](https://dorar.net/feqhia/13753) keeps spouse exclusion, school attribution and treasury qualifications together | Adds a more explicit definition alongside UQU; Kuwaiti's bounded definition remains available |
| الوارث | No direct standalone definition found | [13655](https://dorar.net/feqhia/13655): «الوارِثُ أحَدُ أركانِ الميراثِ» | [13665](https://dorar.net/feqhia/13665) separately explains the survival condition with an example; neither is promoted as a complete definition | Kuwaiti already has the exact الوارث definition |
| التركة | No direct definition under this term found | [13638](https://dorar.net/feqhia/13638) defines الإرث, not a complete independent definition of التركة | Distribution chapters give methods; several worked tables are images | Existing Kuwaiti estate definition is preferable |
| أصل المسألة | Procedure found; no direct definition found | [13736](https://dorar.net/feqhia/13736): «لاستِخراجِ أصلِ المَسألةِ نَتَّبِعُ الخُطُواتِ الآتيةَ» | Complete text-only numerical ratio examples are usable as educational examples, not solver rules | Kuwaiti already contains a direct definition |
| الفرع الوارث | No complete direct definition found | [13700](https://dorar.net/feqhia/13700) mentions it within fixed-share conditions | Term mentions and conditions are insufficient as an independent definition | Kuwaiti has a bounded contextual list; its qualification remains necessary |

## Validation and files

Full backend suite: **489 passed**. Python compilation checks also passed. Tests cover scope isolation, source URL
validation, robots refusal, cache reuse, article-only extraction, exact hashes,
bundled qualifications, oversized-block quarantine, image-table limitations,
definition labeling, bounded ranking and safe source-only synchronization.
Live model outputs are manually assessed below; passing automated tests does
not certify every generated religious claim.

Files created:

- `backend/rag/dorar_ingestion.py`
- `backend/rag/dorar_retrieval.py`
- `backend/data/dorar_fiqhia.metadata.json`
- `tests/test_dorar_ingestion.py`
- `evaluation/check_dorar_live.py`
- `evaluation/dorar_inheritance_report.md`

Files updated:

- `backend/rag/educational_context.py`
- `requirements.txt` (`lxml`)
- `tests/conftest.py` (isolate local source corpus during tests)

No solver, executable rules, model/configuration, request understanding,
claim guard, Quran adapter, frontend or API schema changes in this task.
Other existing worktree changes predate this integration.

## Final live production audit

All seven requests used real BGE-M3/Qdrant retrieval and the unchanged Qwen model through production run_request. Every API response reported supported, and the existing guard blocked no claims. Manual review below overrides that flag for audit purposes. These quoted model answers are observed outputs, not approved religious content.

After synchronizing the site's declared canonical URLs, retrieval was repeated
for all seven frozen semantic requests: selected exact texts and their order
were unchanged in **7/7** checks. Current canonical provenance is retained in
the ignored `processed/post_canonical_retrieval.json`; the original live
transcript retains the URLs returned during generation.

The complete selected chunk texts, exact excerpts, response citations and debug traces are in the ignored local processed/live_validation.json. The table lists the first three actual production chunks; additional selected evidence and original-question-only Dorar candidates are retained in that artifact.

| Question | First three selected chunks / citations | Manual result |
| --- | --- | --- |
| من هم أصحاب الفروض؟ | مقرر المواريث 1 / المواريث / p.7; مقرر المواريث 1 / المواريث / p.7; [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: تَعريفُ الإرثِ وعِلمِ المَواريثِ (الفَرائِضِ)](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29) | partial_category_list |
| ايش معنى الفرض؟ | [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29); مقرر المواريث 1 / المواريث / p.28; [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: تَعريفُ الإرثِ وعِلمِ المَواريثِ (الفَرائِضِ)](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29) | pass |
| فهمني العصبة | [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29); [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: تَعريفُ الحِسابِ لُغةً واصطِلاحًا](https://dorar.net/feqhia/13727); مقرر المواريث 1 / المواريث / p.13 | fail_unsupported_claims |
| وش هو التعصيب؟ | [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29); مقرر المواريث 1 / المواريث / p.13; [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: تَعريفُ الحِسابِ لُغةً واصطِلاحًا](https://dorar.net/feqhia/13727) | review_terminology |
| كيف يعمل الحجب؟ | [الموسوعة الفقهية - الدرر السنية / المبحث الأول: مَعنى الحَجبِ](https://dorar.net/feqhia/13711); [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29); [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: حَجبُ النُّقصانِ](https://dorar.net/feqhia/13716) | review_scope_and_wording |
| ايش هي العول؟ | [الموسوعة الفقهية - الدرر السنية / المطلب الأوَّلُ: مَعنى العَولِ](https://dorar.net/feqhia/13744); مقرر المواريث 1 / المواريث / p.22; [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29) | pass |
| وش يعني الرد؟ | [الموسوعة الفقهية - الدرر السنية / تَعريفُ عِلمِ المَواريثِ (الفَرائِضِ):](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29); مقرر المواريث 1 / المواريث / p.23; [الموسوعة الفقهية - الدرر السنية / المَبحَثُ الأوَّلُ: تَعريفُ الإرثِ وعِلمِ المَواريثِ (الفَرائِضِ)](https://dorar.net/feqhia/13638/%D8%A7%D9%84%D9%85%D8%A8%D8%AD%D8%AB-%D8%A7%D9%84%D8%A3%D9%88%D9%84-%D8%AA%D8%B9%D8%B1%D9%8A%D9%81-%D8%A7%D9%84%D8%A5%D8%B1%D8%AB-%D9%88%D8%B9%D9%84%D9%85-%D8%A7%D9%84%D9%85%D9%88%D8%A7%D8%B1%D9%8A%D8%AB-%28%D8%A7%D9%84%D9%81%D8%B1%D8%A7%D8%A6%D8%B6%29) | fail_changed_condition |

Observed answers and review notes:


### من هم أصحاب الفروض؟

> أصحاب الفروض هم 11 شخصًا، وهم: الزوج، الزوجة، الأم، الأب، الجدة، الجد، البنت، بنت الابن، الأخت الشقيقة، الأخت لأب، والإخوة لأم.

UQU enumeration is reproduced, but it is not a complete category definition.


### ايش معنى الفرض؟

> الفرض هو نصيب مقدر شرعاً لوارث مخصوص، ولا يزيد إلا بالرد ولا ينقص إلا بالعول.

Definition and both adjustment qualifications match supplied evidence.


### فهمني العصبة

> العصبة هي مجموعة من الأقارب الذين يرثون المال إذا لم تبقَ لهم وارثون آخرون.
> وتنقسم العصبة إلى قسمين: العصبة بالنفس، والعمالة بالغير.
> العصبة بالنفس تشمل الأقارب الأقربين مثل البنات والأبناء والأعمام والأب والأخوة، بينما العصبة بالغير تشمل الأقارب الأبعد مثل البنات والبنات من البنات.
> وتنقسم العصبة أيضًا إلى ثلاث فئات: العصبة بالنسب، والعصبة بالغير، والعصبة مع الغير.

Invents eligibility conditions and misstates residuary categories.


### وش هو التعصيب؟

> التعصيب هو من يرث بغير تقدير، بحيث إذا انفرد أخذ المال كله، وإذا كان معه صاحب فرض أخذ ما بقي بعد صاحب الفرض، فإن استغرقت الفروض التركة سقط.

Conditions are supported; defining an inheritance method as a person is imprecise.


### كيف يعمل الحجب؟

> الحجب هو ممنع من قام به سبب الإرث من الإرث بالكلية، أو من أوفى حظّيه.
> ويُقصد به منع وارث من حظّه المقدر إلى حظّ أقل منه، سواءً كان بسبب وجود حاجب أو لمُزاحمة الورَثة، وباتّفاق المذاهيب الفقهية الأربعة.

Contains wording errors and conflates the broader definition with reduction behavior.


### ايش هي العول؟

> العول هو زيادة في سهام الفروض على أصل المسألة، مما يؤدي إلى نقص في نصيب كل وارث.
> وهو مأخوذ من الميل، حيث تميل الفريضة على أهلها جميعًا في الحساب.

Definition and proportional reduction are supported by selected evidence.


### وش يعني الرد؟

> الرد يعني بقاء مال من التركة بعد قسمتها، وهو صرف ما فضل من فروض ذوي الفروض النسبية إليهم بقدر حقوهم، عند عدم استحقاق الغير.

The no-residuary qualification is replaced with an unsupported broader condition; relative fixed-share wording is not in the selected text.

