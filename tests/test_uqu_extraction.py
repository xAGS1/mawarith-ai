import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from backend.rag import uqu_extraction as extraction


def test_font_mapping_uses_glyphs_not_word_replacements():
    font = Mock()
    font.__getitem__ = Mock(return_value=SimpleNamespace(tables=[
        SimpleNamespace(isUnicode=lambda: True, cmap={0xFEEA: 'heh', 0x0661: 'one'}),
        SimpleNamespace(isUnicode=lambda: False, cmap={0x062F: 'heh'})]))
    font.getGlyphID.side_effect = {'heh': 510, 'one': 206}.__getitem__
    assert extraction.glyph_unicode_map(font) == {510: 'ه', 206: '1'}


def test_ambiguous_font_mapping_is_not_guessed():
    font = Mock()
    font.__getitem__ = Mock(return_value=SimpleNamespace(tables=[
        SimpleNamespace(isUnicode=lambda: True, cmap={0x062F: 'shared', 0x0645: 'shared'})]))
    font.getGlyphID.return_value = 7
    assert extraction.glyph_unicode_map(font) == {}


@pytest.mark.parametrize('font', [{}, {'/Encoding': '/WinAnsiEncoding'},
    {'/Encoding': '/Identity-H', '/ToUnicode': True, '/DescendantFonts': []}])
def test_unsupported_font_encoding_is_unchanged(font):
    before = dict(font)
    assert extraction.repair_font(font) == 0
    assert font == before


def test_wrong_document_hash_rejected(tmp_path):
    pdf = tmp_path / 'changed.pdf'
    pdf.write_bytes(b'not approved')
    with pytest.raises(ValueError, match='hash mismatch'):
        extraction.extract_pages(pdf, {'document_sha256': '0' * 64})


def test_unrecoverable_encoding_is_flagged_without_rewriting():
    damaged = 'ْو أن ٚنقسم العدد الكبٛر'
    assert extraction.extraction_warnings(damaged)
    assert not extraction.extraction_warnings('العول هو زيادة في أصل المسألة 12 و24')
    assert not extraction.extraction_warnings('قرآنٌ آياتٌ بَيِّناتٌ')


def test_damaged_pages_are_not_retrieval_context():
    from backend.rag.educational_context import source_windows
    records = [{'text': 'damaged', 'source': {'retrieval_eligible': False}},
               {'text': 'readable', 'source': {}}]
    assert [r['text'] for r in source_windows(records)] == ['readable']


def test_actual_approved_uqu_pages_have_readable_text_and_numeric_order():
    root = Path(__file__).resolve().parents[1]
    pdf = root / 'data/fiqh/uqu_mawarith_1/raw/mawarith_course-uqu.pdf'
    if not pdf.exists():
        pytest.skip('Local approved UQU PDF is not redistributed')
    metadata = json.loads((root / 'backend/data/uqu_mawarith_1.metadata.json').read_text(encoding='utf-8'))
    before = hashlib.sha256(pdf.read_bytes()).hexdigest()
    pages = extraction.extract_pages(pdf, metadata)
    awl = pages[21]['text']
    assert 'زيادة في أصل المسألة' in awl
    assert 'ونضعه بدل الأصل' in awl
    assert '12' in awl and '24' in awl and '27' in awl
    assert '1/2' in awl and '1/3' in awl
    for old in ['ادلسألة', 'الدسألة', 'تعريفو', 'نضعو', 'ٙ', 'ٛ', 'ٔ/ٕ']:
        assert old not in awl
    assert 'الإرث بغير تقدير' in pages[12]['text']
    assert 'منع الوارث من الإرث كله أو بعضه' in pages[12]['text']
    assert 'بقاء مال من التركة بعد قسمتها' in pages[22]['text']
    assert 'أصحاب الفروض' in pages[6]['text'] and '1/8' in pages[6]['text']
    assert 'هو نصيب مقدر شرعا لوارث مخصوص' in pages[27]['text']
    assert hashlib.sha256(pdf.read_bytes()).hexdigest() == before
    for record in pages:
        assert record['source']['document_sha256'] == before
        assert record['source']['text_sha256'] == hashlib.sha256(record['text'].encode()).hexdigest()
    assert [p['source']['page'] for p in pages if not p['source']['retrieval_eligible']] == [3, 15]
