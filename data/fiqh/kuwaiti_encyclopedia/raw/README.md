# Place approved source files here

Do not create or paraphrase fiqh content.
Only locally supplied, approved excerpts from الموسوعة الفقهية الكويتية may be
ingested. Publisher: وزارة الأوقاف والشؤون الإسلامية - الكويت.

Supported formats: UTF-8 `.txt`, `.md`, `.json`, or Word `.docx`. TXT/Markdown requires a JSON
sidecar named `filename.txt.metadata.json` or `filename.md.metadata.json`.
JSON files contain one full source record or a list of records, including `text`.
The ingestion tool skips README.md and metadata sidecars as content.

Required metadata: `source_type: "fiqh"`, the exact `source_name` and `publisher`
above, `source_url` (real source URL), `topic`, `volume`, and `verified_source: true`.
`page` and `section` are optional and default to null. Unknown volume/page/section must be explicitly null;
volume/page, when supplied, must be positive integers. Approval is a human
provenance assertion; the software cannot certify a document's authenticity.

The source text is read verbatim. Do not put guessed URLs, fabricated page
numbers, generated summaries, or model-produced religious text in this folder.

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
