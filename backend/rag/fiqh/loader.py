"""Ingest approved local UTF-8 sources; no downloading or generated content."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from pydantic import ValidationError

from backend.rag.fiqh.chunker import chunk_record
from backend.rag.fiqh.schemas import FiqhSourceRecord


DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "fiqh" / "kuwaiti_encyclopedia"


def read_utf8(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as file:
        return file.read()


def read_docx(path: Path, diagnostics=None, section_spans=None) -> str:
    """Keep each body paragraph's extracted text verbatim and in document order."""
    try:
        from docx import Document
        from docx.text.paragraph import Paragraph
    except ImportError as exc:
        raise ValueError("DOCX ingestion requires python-docx; install requirements-fiqh.txt") from exc
    try:
        document = Document(path)
        # Traverse physical XML paragraphs once: document order includes table
        # cells/nested tables, without duplicating merged cells via row.cells.
        objects = [Paragraph(element, document) for element in document.element.body.xpath(".//w:p")]
        paragraphs = [paragraph.text for paragraph in objects]
        offset = 0
        for paragraph in objects:
            if paragraph.text == "":
                continue
            # نمط3 is the inspected article-title style in this converted corpus.
            style = paragraph.style.name if paragraph.style else ""
            if section_spans is not None and (style == "نمط3" or style.startswith("Heading") or paragraph._p.xpath("./w:pPr/w:outlineLvl")):
                section_spans.append((offset, paragraph.text))
            offset += len(paragraph.text) + 2
        nonempty = [text for text in paragraphs if text != ""]
        if diagnostics:
            diagnostics(f"Loaded {len(nonempty)} nonempty paragraphs ({len(paragraphs)} total, {len(document.tables)} tables) from {path.name}")
        return "\n\n".join(nonempty)
    except Exception as exc:
        raise ValueError(f"Cannot extract DOCX paragraphs from {path}: {exc}") from exc


def load_source_file(path: Path, diagnostics=None, section_spans=None) -> list[dict]:
    if path.suffix.lower() == ".json":
        data = json.loads(read_utf8(path))
        records = data if isinstance(data, list) else [data]
    elif path.suffix.lower() in (".txt", ".md", ".docx"):
        metadata_path = path.with_name(path.name + ".metadata.json")
        if diagnostics:
            diagnostics(f"Metadata sidecar: {metadata_path}")
        if not metadata_path.is_file():
            raise ValueError(f"Missing provenance sidecar: {metadata_path}")
        try:
            metadata = json.loads(read_utf8(metadata_path))
        except ValueError as exc:
            raise ValueError(f"Invalid provenance JSON: {metadata_path}") from exc
        if not isinstance(metadata, dict) or "text" in metadata:
            raise ValueError("Text sidecars must contain metadata only")
        text = read_docx(path, diagnostics, section_spans) if path.suffix.lower() == ".docx" else read_utf8(path)
        records = [{**metadata, "text": text}]
    else:
        raise ValueError(f"Unsupported source format: {path.suffix}")
    return [FiqhSourceRecord.model_validate(r).model_dump(mode="json") for r in records]


def ingest(raw_dir: Path = DATA_DIR / "raw", output: Path = DATA_DIR / "processed" / "chunks.json", diagnostics=None) -> int:
    if not raw_dir.is_dir():
        raise ValueError(f"Source directory does not exist or is inaccessible: {raw_dir}")
    # os.walk's default skips discovery errors; explicitly propagate them.
    def discovery_error(error):
        raise error

    discovered = [Path(directory) / name for directory, _, names in os.walk(raw_dir, onerror=discovery_error) for name in names]
    files = sorted(p for p in discovered if p.is_file()
                   and p.resolve() != output.resolve()
                   and p.suffix.lower() in (".txt", ".md", ".json", ".docx")
                   and p.name.lower() != "readme.md"
                   and not p.name.endswith(".metadata.json"))
    if diagnostics:
        diagnostics(f"Found {len(files)} source document(s) in {raw_dir}")
    chunks = []
    for path in files:
        try:
            sections = []
            records = load_source_file(path, diagnostics, sections)
            if not records:
                raise ValueError(f"Source file contains no records: {path}")
            if diagnostics:
                diagnostics(f"Validated {len(records)} source record(s) from {path.name}; chunking...")
            document_chunks = []
            for record in records:
                document_chunks.extend(chunk_record(record, path.relative_to(raw_dir).as_posix(), section_spans=sections))
            if not document_chunks:
                raise ValueError(f"No chunks produced for source file: {path}")
            chunks.extend(document_chunks)
            if diagnostics:
                diagnostics(f"Created {len(document_chunks)} chunks from {path.name}")
        except ValidationError:
            raise
        except (ValueError, OSError) as exc:
            raise ValueError(f"Ingestion failed for {path}: {exc}") from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as file:
            temporary_path = Path(file.name)
            json.dump(chunks, file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, output)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    if diagnostics:
        diagnostics(f"Created {len(chunks)} chunks total")
        diagnostics(f"Wrote {output} ({output.stat().st_size} bytes)")
    return len(chunks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=DATA_DIR / "raw")
    parser.add_argument("--out", type=Path, default=DATA_DIR / "processed" / "chunks.json")
    args = parser.parse_args()
    try:
        count = ingest(args.raw_dir, args.out, diagnostics=lambda message: print(message, flush=True))
    except ValidationError as exc:
        errors = "; ".join(f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in exc.errors(include_input=False, include_url=False))
        print(f"Metadata/source validation failed: {errors}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc
    except (ValueError, OSError) as exc:
        print(f"Ingestion error: {exc}", file=sys.stderr, flush=True)
        raise SystemExit(1) from exc
    print(f"Ingested {count} exact-text chunks into {args.out}")


if __name__ == "__main__":
    main()
