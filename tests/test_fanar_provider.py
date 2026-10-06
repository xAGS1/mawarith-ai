import json
import requests
import pytest
from backend.llm import transport, fanar, provider

@pytest.fixture(autouse=True)
def config(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER','fanar')
    monkeypatch.setenv('FANAR_API_KEY','test-secret-not-real')
    monkeypatch.setenv('LLM_FALLBACK_PROVIDER','none')

class Response:
    status_code=200
    ok=True
    def json(self):
        return {'model':'Fanar-C-2-27B','choices':[{'message':{'content':'{"answer":"ok"}'}}], 'usage':{'prompt_tokens':7,'completion_tokens':3}}


def test_success(monkeypatch):
    captured={}
    def post(url,**kwargs):
        captured.update(url=url,**kwargs)
        return Response()
    monkeypatch.setattr(requests,'post',post)
    assert json.loads(transport.generate([{'role':'system','content':'test'},{'role':'user','content':'question'}],response_format={'type':'object'}))=={'answer':'ok'}
    assert captured['url'].endswith('/chat/completions')
    assert captured['json']['model']=='Fanar-C-2-27B'
    assert transport.LAST_GENERATION.get()['completion_tokens']==3

@pytest.mark.parametrize('status',[401,429])
def test_http_error_safe_no_fallback(monkeypatch,status,caplog):
    calls=[]
    def post(*a,**k):
        calls.append(a)
        r=Response(); r.status_code=status; r.ok=False
        return r
    monkeypatch.setattr(requests,'post',post)
    with pytest.raises(transport.ProviderError) as exc:
        transport.generate([{'role':'system','content':'test'}])
    assert len(calls)==1
    assert 'test-secret' not in str(exc.value)+caplog.text
    assert exc.value.request is None and exc.value.response is None

@pytest.mark.parametrize('kind',['timeout','malformed','invalid_json'])
def test_failures(monkeypatch,kind):
    def post(*a,**k):
        if kind=='timeout': raise requests.Timeout('private raw response')
        r=Response()
        r.json=lambda: {} if kind=='malformed' else {'choices':[{'message':{'content':'not JSON'}}]}
        return r
    monkeypatch.setattr(requests,'post',post)
    with pytest.raises(transport.ProviderError):
        transport.generate([{'role':'system','content':'test'}],response_format={'type':'object'})


def test_ollama_and_explicit_fallback(monkeypatch):
    calls=[]
    def post(url,**k):
        calls.append(url)
        if 'fanar' in url: raise requests.Timeout()
        r=Response(); r.json=lambda:{'message':{'content':'local'},'eval_count':2}
        return r
    monkeypatch.setattr(requests,'post',post)
    monkeypatch.setenv('LLM_PROVIDER','ollama')
    assert transport.generate([{'role':'system','content':'test'}])=='local'
    monkeypatch.setenv('LLM_PROVIDER','fanar')
    monkeypatch.setenv('LLM_FALLBACK_PROVIDER','ollama')
    assert transport.generate([{'role':'system','content':'test'}])=='local'
    assert len(calls)==3


def test_selection_and_legacy_alias(monkeypatch):
    for value,expected in [('fanar','fanar'),('ollama','ollama'),('qwen','ollama')]:
        monkeypatch.setenv('LLM_PROVIDER',value)
        assert transport.selected_provider()==expected
    monkeypatch.setenv('LLM_PROVIDER','unknown')
    with pytest.raises(transport.ProviderError): transport.selected_provider()


def test_invalid_explanation_citations(monkeypatch):
    monkeypatch.setattr(provider,'generate',lambda *a,**k:json.dumps({'status':'ready','answer':'test','evidence_ids':['E99'],'key_concepts':[]}))
    with pytest.raises(ValueError): provider.explain_context('question','ar',[{'evidence_id':'E1','text':'source'}])

def test_structured_task_gateway(monkeypatch):
    from backend.llm.generation_capacity import generation_post
    captured={}
    def post(url,**kwargs):
        captured.update(kwargs['json'])
        return Response()
    monkeypatch.setattr(requests,'post',post)
    response=generation_post('http://localhost:11434/api/generate',json={
        'system':'understand input','prompt':'question','format':{'type':'object'},
        'options':{'num_predict':400,'temperature':0}})
    response.raise_for_status()
    assert json.loads(response.json()['response'])=={'answer':'ok'}
    assert captured['max_tokens']==400
    assert 'schema' in captured['messages'][0]['content']


def test_missing_key_no_request(monkeypatch):
    monkeypatch.delenv('FANAR_API_KEY')
    monkeypatch.setattr(requests,'post',lambda *a,**k:pytest.fail('Must not send without a key'))
    with pytest.raises(transport.ProviderError):
        transport.generate([{'role':'system','content':'test'}])
