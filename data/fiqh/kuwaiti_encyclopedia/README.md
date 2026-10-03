# Approved local Kuwaiti Fiqh Encyclopedia corpus

This corpus is currently empty. No fiqh source content is provided or generated
by this project. Initial approved source: الموسوعة الفقهية الكويتية; official
publisher: وزارة الأوقاف والشؤون الإسلامية - الكويت.

Place locally approved verbatim excerpts in `raw/`. Formats are UTF-8 TXT,
Markdown and JSON. TXT/Markdown requires a sidecar named
`file.txt.metadata.json` or `file.md.metadata.json`. JSON can contain a single
source record or an array of records, with the exact `text` field.

Every source requires `source_type: "fiqh"`, the exact approved `source_name`
and `publisher`, `source_url`, `topic`, `volume`, `page`, `section`, and
`verified_source: true`. Explicit null values are permitted for unavailable
volume/page/section; known volume/page values must be positive integers. No
metadata is guessed. The user must verify source provenance before marking it
approved. Metadata validation does not itself authenticate a publication.

Text must be real source text supplied locally. No scraping, downloads of
arbitrary third-party copies, generated summaries or invented religious text.
Runtime source files and processed chunks are ignored by Git.

From the project root, ingest, index, and test retrieval:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.loader
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.vector_store
.\.venv\Scripts\python.exe -X utf8 -m backend.rag.fiqh.retriever
```

Ingestion writes exact-text chunks to `processed/chunks.json`. Approximate
Arabic subword budgets target 550 tokens (at most 700) and about 80 overlap,
preferring paragraphs and sentence boundaries. Exact character slices, original
document SHA-256 and offsets are retained. Token counts are estimates, not
claims about BGE-M3's exact tokenizer counts. A sentence exceeding the budget
can be split at word boundaries; no source characters are rewritten.

Indexing uses local BGE-M3 dense embeddings (1024 dimensions) and a real Qdrant
collection, `mawarith_fiqh`, with cosine distance and full metadata payloads.
Point IDs are deterministic. Reindexing replaces matching IDs but does not
delete older points; retrieval validates hits against the current local corpus
and rejects stale or altered payloads. Use a fresh configured collection after
changing models or corpus structure; collections are never silently recreated.

Empty corpus behavior: ingestion writes `[]`, indexing reports zero chunks,
and retrieval returns `[]` without loading an embedding model or contacting
Qdrant. With a nonempty corpus, Qdrant/model failures raise explicit errors.
The main pipeline reports evidence retrieval errors under `fiqh_retrieval`
and may continue using covered structured rules; it does not fake evidence.

Fiqh retrieval is supporting evidence only. It never determines shares or
satisfies structured inheritance coverage. Final evidence preserves exact text
outside the model-generated result. Curated fiqh-backed inheritance rules need
separate review before being added to the authoritative rule library.
