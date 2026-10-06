"""Selected LLM tasks; public task contracts remain unchanged."""
import json
from backend.llm.transport import generate, selected_provider


def explain_context(question, language, evidence, verified_result=None):
    if selected_provider() == 'ollama':
        from backend.llm import qwen_explainer
        return qwen_explainer.explain_context(question,language,evidence,verified_result)
    system='''أجب عن السؤال اعتمادًا على الأدلة المرفقة.
- لا تضف حكمًا شرعيًا غير مدعوم بالأدلة.
- إذا كانت الأدلة غير كافية، وضح ذلك.
- حافظ على الشروط والاستثناءات المذكورة في المصادر.
- أجب بلغة السؤال بشكل واضح ومختصر.
Use supplied evidence IDs as citations [E1] and list them in evidence_ids.
Return JSON: status (ready or insufficient_evidence), answer, evidence_ids, key_concepts (empty array).'''
    if verified_result is not None:
        system += '\nExplain only the verified_result. Never calculate or change fractions, heirs or distribution.'
    schema={'type':'object','properties':{'status':{'type':'string','enum':['ready','insufficient_evidence']},
        'answer':{'type':'string'},'evidence_ids':{'type':'array','items':{'type':'string'}},'key_concepts':{'type':'array'}},
        'required':['status','answer','evidence_ids','key_concepts']}
    from backend.llm.generation_capacity import _capacity
    with _capacity:
        raw=generate([{'role':'system','content':system},{'role':'user','content':json.dumps(
            {'question':question,'language':language,'evidence':evidence,'verified_result':verified_result},ensure_ascii=False)}],
            600,0,schema)
    result=json.loads(raw)
    if (result.get('status') not in {'ready','insufficient_evidence'} or not isinstance(result.get('answer'),str)
        or not isinstance(result.get('evidence_ids'),list) or result.get('key_concepts') != []
        or any(i not in {e['evidence_id'] for e in evidence} for i in result['evidence_ids'])):
        raise ValueError('Invalid structured explanation')
    return result


def explain(question, language, evidence):
    if selected_provider() == 'ollama':
        from backend.llm import qwen_explainer
        return qwen_explainer.explain(question,language,evidence)
    return explain_context(question,language,evidence)
