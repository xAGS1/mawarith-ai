from backend.pipeline.fanar_sentence_check import check_cited_support
from backend.pipeline.educational_claims import filter_claims


def test_distant_paraphrase_not_rejected_for_wording():
    evidence=[{'evidence_id':'E1','text':'الفرض: الإرث بتقدير.'}]
    answer='الفرض يشير إلى حصول الوارث على حصة محددة من الميراث [E1].'
    kept,removed=check_cited_support(answer,evidence)
    assert kept==answer and not removed


def test_multiline_supported_enumeration():
    evidence=[{'evidence_id':'E1','text':'ثلاثة أنواع\n1- أول\n2- ثان\n3- ثالث'}]
    assert check_cited_support('هناك ثلاثة أنواع: أول، ثان، ثالث [E1].',evidence)[0]


def test_invalid_and_missing_evidence_still_rejected():
    assert check_cited_support('قول [E99].',[{'evidence_id':'E1','text':'نص'}])[1]
    assert check_cited_support('قول.',[])[1]


def test_explicit_negation_contradiction():
    evidence=[{'evidence_id':'E1','text':'لا يستحق هذا الشخص المال.'}]
    assert check_cited_support('يستحق هذا الشخص المال [E1].',evidence)[1]


def test_fabricated_consensus_attribution():
    evidence=[{'evidence_id':'E1','text':'تعريف تعليمي'}]
    assert check_cited_support('أجمع الفقهاء على هذا الحكم [E1].',evidence)[1]


def test_numerical_claim_guard_remains_active():
    evidence=[{'evidence_id':'E1','text':'تعريف تعليمي'}]
    answer=check_cited_support('نصيب الزوجة 1/4 [E1].',evidence)[0]
    assert not filter_claims(answer,evidence)[0]


def test_provider_specific_production_orchestration(monkeypatch):
    from backend.pipeline import rag_answer
    from backend.pipeline.semantic_request import SemanticRequest
    request=SemanticRequest(intent='educational',language='ar',topic='',retrieval_query='question',concepts=[],case=None,clarification_question=None)
    evidence=[{'evidence_id':'E1','text':'الفرض: الإرث بتقدير.','provenance':{'source_name':'test'}}]
    monkeypatch.setattr(rag_answer,'retrieve_context',lambda *a:evidence)
    monkeypatch.setattr(rag_answer.provider,'explain_context',lambda *a:{'status':'ready','answer':'الفرض يشير إلى حصة محددة من الميراث [E1].','evidence_ids':['E1']})
    from backend.llm.transport import LAST_GENERATION
    LAST_GENERATION.set(None)
    for provider in ('fanar','ollama','qwen'):
        monkeypatch.setenv('LLM_PROVIDER',provider)
        expected = 'supported' if provider == 'fanar' else 'insufficient'
        assert rag_answer.answer_educational('اشرح الفرض',request)['evidence_status'] == expected

def test_explicit_ollama_fallback_keeps_strict_policy(monkeypatch):
    from backend.pipeline import rag_answer
    from backend.pipeline.semantic_request import SemanticRequest
    from backend.llm.transport import LAST_GENERATION
    request=SemanticRequest(intent='educational',language='ar',topic='',retrieval_query='question',concepts=[],case=None,clarification_question=None)
    evidence=[{'evidence_id':'E1','text':'الفرض: الإرث بتقدير.','provenance':{'source_name':'test'}}]
    monkeypatch.setenv('LLM_PROVIDER','fanar')
    monkeypatch.setattr(rag_answer,'retrieve_context',lambda *a:evidence)
    def local_fallback(*a):
        LAST_GENERATION.set({'provider':'ollama'})
        return {'status':'ready','answer':'الفرض يشير إلى حصة محددة من الميراث [E1].','evidence_ids':['E1']}
    monkeypatch.setattr(rag_answer.provider,'explain_context',local_fallback)
    trace={}
    assert rag_answer.answer_educational('اشرح الفرض',request,trace)['evidence_status']=='insufficient'
    assert trace['sentence_screen_policy']=='qwen_strict_lexical'


def test_qwen_original_supported_sentence_and_extra_claim(monkeypatch):
    from backend.pipeline import rag_answer
    from backend.pipeline.semantic_request import SemanticRequest
    request=SemanticRequest(intent='educational',language='ar',topic='',retrieval_query='question',concepts=[],case=None,clarification_question=None)
    evidence=[{'evidence_id':'E1','text':'اصطلاحا: الإرث بغير تقدير.','provenance':{'source_name':'test'}}]
    monkeypatch.setenv('LLM_PROVIDER','ollama')
    monkeypatch.setattr(rag_answer,'retrieve_context',lambda *a:evidence)
    monkeypatch.setattr(rag_answer.provider,'explain_context',lambda *a:{'status':'ready',
        'answer':'التعصيب هو الإرث بغير تقدير [E1].\nولا يراعي النسب أو العدد [E1].','evidence_ids':['E1']})
    trace={}
    result=rag_answer.answer_educational('اشرح التعصيب',request,trace)
    assert result['evidence_status']=='supported'
    assert 'النسب' not in result['answer']
    assert trace['sentence_screen_policy']=='qwen_strict_lexical'
    assert trace['sentence_screen_removals'][0]['reason']=='uncertain_sentence_support'
