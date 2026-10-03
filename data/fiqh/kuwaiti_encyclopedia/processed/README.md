# Processed runtime artifacts

`python -m backend.rag.fiqh.loader` writes `chunks.json` here. With no approved
source files it contains an empty list. Generated artifacts are ignored by Git.
Each chunk retains exact text, source metadata, document checksum and offsets.
