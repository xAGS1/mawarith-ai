"""Ingest approved local UTF-8 sources; no downloading or generated content."""

import argparse
import json
from pathlib import Path

from backend.rag.fiqh.chunker import chunk_record
from backend.rag.fiqh.schemas import FiqhSourceRecord


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "fiqh" / "kuwaiti_encyclopedia"


def read_utf8(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


def load_source_file(path: Path) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(read_utf8(path))
        records = data if isinstance(data, list) else [data]
    elif path.suffix.lower() in (".txt", ".md"):
        metadata_path = path.with_name(path.name + ".metadata.json")
        if not metadata_path.is_file():
            raise ValueError(f"Missing provenance sidecar: {metadata_path}")
        metadata = json.loads(read_utf8(metadata_path))
        if not isinstance(metadata, dict) or "text" in metadata:
            raise ValueError("Text sidecars must contain metadata only")
        records = [{**metadata, "text": read_utf8(path)}]
    else:
        raise ValueError(f"Unsupported source format: {path.suffix}")
    return [FiqhSourceRecord.model_validate(r).model_dump(mode="json") for r in records]


def ingest(raw_dir: Path = DATA_DIR / "raw", output: Path = DATA_DIR / "processed" / "chunks.json") -> int:
    files = sorted(p for p in raw_dir.rglob("*") if p.is_file()
                   and p.suffix.lower() in (".txt", ".md", ".json")
                   and p.name.lower() != "readme.md"
                   and not p.name.endswith(".metadata.json"))
    chunks = []
    for path in files:
        for record in load_source_file(path):
            chunks.extend(chunk_record(record, path.relative_to(raw_dir).as_posix()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DATA_DIR / "raw")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "processed" / "chunks.json")
    args = parser.parse_args()
    try:
        count = ingest(args.raw_dir, args.out)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Ingested {count} exact-text chunks into {args.out}")


if __name__ == "__main__":
    main()
