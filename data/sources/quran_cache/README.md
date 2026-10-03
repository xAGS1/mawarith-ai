# QuranEnc runtime cache

Fetched verses are stored as `surah_ayah.json`, for example `4_12.json`.
Runtime files are ignored by Git. Arabic text is copied exactly from QuranEnc's
`arabic_text` field without normalization, paraphrasing, or model involvement.
Records include provider, verse identity, retrieval timestamp and a SHA-256
checksum to detect accidental corruption. Writes replace files atomically.
An invalid cache is refetched; failed retrieval never creates substitute text.
