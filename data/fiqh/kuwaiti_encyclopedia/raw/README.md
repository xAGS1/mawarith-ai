# Place approved source files here

There is currently no approved corpus. Do not create or paraphrase fiqh content.
Only locally supplied, approved excerpts from الموسوعة الفقهية الكويتية may be
ingested. Publisher: وزارة الأوقاف والشؤون الإسلامية - الكويت.

Supported formats: UTF-8 `.txt`, `.md`, or `.json`. TXT/Markdown requires a JSON
sidecar named `filename.txt.metadata.json` or `filename.md.metadata.json`.
JSON files contain one full source record or a list of records, including `text`.
The ingestion tool skips README.md and metadata sidecars as content.

Required metadata: `source_type: "fiqh"`, the exact `source_name` and `publisher`
above, `source_url` (real source URL), `topic`, `volume`, `page`, `section`, and
`verified_source: true`. Unknown volume/page/section must be explicitly null;
volume/page, when supplied, must be positive integers. Approval is a human
provenance assertion; the software cannot certify a document's authenticity.

The source text is read verbatim. Do not put guessed URLs, fabricated page
numbers, generated summaries, or model-produced religious text in this folder.
