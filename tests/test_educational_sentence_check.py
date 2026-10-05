from backend.pipeline.educational_sentence_check import check_sentences, check_consistency


def test_short_paraphrase_survives_extra_claim_does_not():
    evidence = [{'evidence_id':'E1','text':'اصطلاحا: الإرث بغير تقدير.'}]
    answer = 'التعصيب هو الإرث بغير تقدير [E1].\nولا يراعي النسب أو العدد [E1].'
    kept, removed = check_sentences(answer, evidence)
    assert 'التعصيب هو' in kept
    assert 'النسب' not in kept and len(removed)==1


def test_supported_rewording_need_not_be_verbatim():
    evidence = [{'evidence_id':'E1','text':'للبنت الواحدة النصف عند عدم وجود ابن.'}]
    kept, _ = check_sentences('يكون نصيب البنت الواحدة النصف عندما لا يوجد ابن [E1].', evidence)
    assert kept


def test_generic_connective_is_not_mistaken_for_article_prefix():
    evidence = [{'evidence_id':'E1','text':'العنوان\nواصطلاحا: زيادة في المقدار ينتج عنها زيادة في الأصل.'}]
    assert check_sentences('العنوان هو زيادة في المقدار تؤدي إلى زيادة في الأصل [E1].', evidence)[0]


def test_uncertain_sentence_and_missing_evidence_are_removed():
    assert not check_sentences('حكم جديد غير مذكور.', [])[0]
    assert not check_sentences('نص جديد [E2].', [{'evidence_id':'E1','text':'نص آخر.'}])[0]


def test_evidence_in_unrelated_paragraphs_cannot_be_joined():
    evidence = [{'evidence_id':'E1','text':'alpha beta.\ngamma delta.'}]
    assert not check_sentences('alpha beta gamma delta [E1].', evidence)[0]


def test_explicit_count_contradiction_is_removed_without_concept_rules():
    kept, removed = check_consistency('تنقسم إلى قسمان: الأول، الثاني، الثالث.\nعبارة مستقلة صحيحة.')
    assert kept == 'عبارة مستقلة صحيحة.' and removed
    assert check_consistency('ثلاثة: الأول، الثاني، الثالث.')[0]
    assert check_consistency('تُقسم إلى قسمين: بالنفس، وبالغير، ومع الغير.')[1]


def test_same_subject_conflicting_fractions():
    kept, removed = check_consistency('النصيب 1/2.\nالنصيب 1/3.')
    assert '1/3' not in kept and removed
    assert not check_consistency('عند الشرط الأول 1/2.\nعند الشرط الآخر 1/3.')[1]
    assert check_consistency('النصيب النصف.\nالنصيب الثلث.')[1]


def test_added_clause_does_not_erase_supported_definition():
    evidence = [{'evidence_id':'E1','text':'اصطلاحا: الإرث بغير تقدير.'}]
    kept, removed = check_sentences('العصبة تعني الإرث بغير تقدير، وهو توزيع دون حساب عدد الأفراد [E1].', evidence, ['E1'])
    assert kept == 'العصبة تعني الإرث بغير تقدير' and removed


def test_negation_and_required_condition_are_not_silently_dropped():
    evidence = [{'evidence_id':'E1','text':'يحدث الأثر عند وجود الشرط.'}]
    assert not check_sentences('يحدث الأثر [E1].', evidence)[0]


def test_definition_can_be_short_without_borrowing_later_behavior():
    evidence = [{'evidence_id':'E1','text':'التعريف: هو وصف الفئة، لا يتغير هذا الوصف.'}]
    assert check_sentences('التعريف هو وصف الفئة [E1].', evidence)[0]
    evidence[0]['text'] = 'التعريف: هو وصف الفئة، بشرط تحقق العلاقة.'
    assert not check_sentences('التعريف هو وصف الفئة [E1].', evidence)[0]
    evidence[0]['text'] = 'لا يحدث الأثر.'
    assert not check_sentences('يحدث الأثر [E1].', evidence)[0]


def test_educational_format_is_internal_and_case_prompt_is_unchanged(monkeypatch):
    import json
    from unittest.mock import Mock
    from backend.llm import qwen_explainer as qwen
    http = Mock()
    http.json.return_value = {'response': json.dumps({'status':'ready','sentences':[
        {'text':'Natural supported sentence.','evidence_ids':['E1']}]})}
    post = Mock(return_value=http)
    monkeypatch.setattr(qwen.requests, 'post', post)
    evidence = [{'evidence_id':'E1','text':'Natural supported sentence.'}]
    response = qwen.explain_context('question','en',evidence)
    assert response['answer']=='Natural supported sentence. [E1]'
    assert response['evidence_ids']==['E1']
    assert 'sentences' in post.call_args.kwargs['json']['format']['properties']
    http.json.return_value = {'response': json.dumps({'status':'ready','answer':'verified','evidence_ids':['E1'],'key_concepts':[]})}
    qwen.explain_context('case','en',evidence,{'verified':True})
    payload = post.call_args.kwargs['json']
    assert 'sentences' not in payload['format']['properties']
    assert 'EDUCATIONAL PRECISION' not in payload['system']
