"""Recover PDF glyph encoding from embedded fonts, never from word substitutions.

The original PDF is immutable. Only Identity-H fonts with an identity CID/GID
map and an unambiguous embedded Unicode cmap are eligible for in-memory repair.
"""
from io import BytesIO
import hashlib
import json
from pathlib import Path
import re
import unicodedata

from fontTools.ttLib import TTFont
from pypdf import PdfReader
from pypdf._cmap import _parse_to_unicode
from pypdf.generic import DecodedStreamObject, NameObject

EXTRACTOR_VERSION = "embedded-cmap-pypdf-v1"


def extraction_warnings(text):
    # Repeated orphan combining marks in running prose indicate an unrecovered
    # glyph encoding. Flag for review; never replace them with guessed letters.
    artifacts = re.findall(r'(?<![\u0621-\u0652])[\u0653-\u065c]|[\u0656-\u065c]', text)
    return ['Unrecovered Arabic glyph encoding; manual review/OCR required'] if len(artifacts) >= 2 else []


def glyph_unicode_map(font):
    candidates = {}
    for table in font['cmap'].tables:
        if not table.isUnicode():
            continue
        for code, name in table.cmap.items():
            # Compatibility normalization is confined to font presentation glyphs.
            char = chr(code)
            value = unicodedata.normalize('NFKC', char) if 0xFB50 <= code <= 0xFEFF else char
            # pypdf reverses Arabic digit runs in RTL spans. Equivalent ASCII
            # digits retain their numeric order through its bidi handling.
            if len(value) == 1 and '\u0660' <= value <= '\u0669':
                value = str(ord(value) - ord('\u0660'))
            candidates.setdefault(font.getGlyphID(name), set()).add(value)
    return {gid: next(iter(values)) for gid, values in candidates.items() if len(values) == 1}


def repair_font(font):
    if font.get('/Encoding') != '/Identity-H' or '/ToUnicode' not in font:
        return 0
    descendants = font.get('/DescendantFonts', [])
    if not descendants:
        return 0
    descendant = descendants[0].get_object()
    if descendant.get('/CIDToGIDMap') != '/Identity':
        return 0
    descriptor = descendant.get('/FontDescriptor')
    if not descriptor or '/FontFile2' not in descriptor:
        return 0
    with TTFont(BytesIO(descriptor['/FontFile2'].get_data())) as embedded:
        recovered = glyph_unicode_map(embedded)
    original, _ = _parse_to_unicode(font)
    mappings = {ord(k): v for k, v in original.items() if isinstance(k, str) and len(k) == 1}
    changes = sum(mappings.get(gid) != value for gid, value in recovered.items() if gid in mappings)
    if not changes:
        return 0
    # Keep mappings for custom ligatures absent from the font cmap unchanged.
    repairs = {gid: value for gid, value in recovered.items() if gid in mappings}
    mappings.update(repairs)
    lines = ['/CIDInit /ProcSet findresource begin', '12 dict begin', 'begincmap',
             '/CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def',
             '/CMapName /RecoveredUnicode def', '/CMapType 2 def',
             '1 begincodespacerange', '<0000> <FFFF>', 'endcodespacerange']
    items = sorted(mappings.items())
    for start in range(0, len(items), 100):
        group = items[start:start + 100]
        lines.append(f'{len(group)} beginbfchar')
        lines.extend(f'<{gid:04X}> <{value.encode("utf-16-be").hex().upper()}>' for gid, value in group)
        lines.append('endbfchar')
    lines.extend(['endcmap', 'CMapName currentdict /CMap defineresource pop', 'end', 'end'])
    stream = DecodedStreamObject()
    stream.set_data('\n'.join(lines).encode('ascii'))
    font[NameObject('/ToUnicode')] = stream
    return sum(original.get(chr(gid)) != value for gid, value in repairs.items())


def extract_pages(path, metadata):
    document = Path(path).read_bytes()
    digest = hashlib.sha256(document).hexdigest()
    if digest != metadata['document_sha256']:
        raise ValueError('UQU source hash mismatch')
    reader = PdfReader(BytesIO(document))
    seen, changed = set(), 0
    for page in reader.pages:
        for ref in page['/Resources'].get('/Font', {}).values():
            key = (getattr(ref, 'idnum', None), getattr(ref, 'generation', None))
            if key in seen:
                continue
            seen.add(key)
            changed += repair_font(ref.get_object())
    records = []
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ''
        source = {**metadata, 'page': number, 'section': None, 'topic': 'المواريث',
                  'extractor_version': EXTRACTOR_VERSION, 'repaired_font_mappings': changed,
                  'chunk_id': hashlib.sha256(f'{digest}:{EXTRACTOR_VERSION}:{number}'.encode()).hexdigest(),
                  'char_start': 0, 'char_end': len(text),
                  'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                  'offset_basis': 'Recovered PDF page text; page is PDF index, not printed folio'}
        source['extraction_warnings'] = extraction_warnings(text)
        source['retrieval_eligible'] = not source['extraction_warnings']
        records.append({'text': text, 'source': source})
    return records


def write_corpus(pdf, metadata_path, output):
    metadata = json.loads(Path(metadata_path).read_text(encoding='utf-8'))
    records = extract_pages(pdf, metadata)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    return records
