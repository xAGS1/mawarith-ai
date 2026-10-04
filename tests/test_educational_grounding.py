import pytest
from backend.pipeline.educational_grounding import check_concept_scope, relevant_public_excerpts


def test_narrower_evidence_does_not_support_general_definition():
    with pytest.raises(ValueError, match="narrower concept"):
        check_concept_scope("ما معنى أصحاب الفروض؟", "شرح أصحاب الفروض [E1]",
                            [{"text": "عنوان اختبار: أصحاب الفروض النسبية"}])


def test_scope_matches_narrow_question():
    check_concept_scope("أصحاب الفروض النسبية", "أصحاب الفروض النسبية [E1]",
                        [{"text": "عنوان اختبار: أصحاب الفروض النسبية"}])


def test_generic_mention_elsewhere_does_not_license_narrow_definition():
    with pytest.raises(ValueError, match="narrower concept"):
        check_concept_scope("ما معنى أصحاب الفروض؟", "شرح أصحاب الفروض [E1]",
                            [{"text": "عنوان اختبار: أصحاب الفروض النسبية\n\nعنوان مرتبط: أصحاب الفروض"}])


def test_exact_paragraph_and_offsets():
    prefix = "محتوى محايد للاختبار. " * 60
    paragraph = "العصبة: فقرة اختبار محايدة دون حكم فقهي."
    text = prefix + "\n\n" + paragraph + "\n\n" + "موضوع مختلف للاختبار."
    record = {"text": text, "evidence_id": "E1", "excerpt_char_start": 20}
    result = relevant_public_excerpts("ما معنى العصبة؟", [record])
    assert result[0]["text"] == paragraph
    assert result[0]["excerpt_char_start"] == 20 + text.index(paragraph)
    assert record["text"] == text


def test_unmatched_large_excerpt_is_omitted():
    assert relevant_public_excerpts("ما معنى العصبة؟", [{"text": "neutral unrelated fixture " * 60}]) == []
