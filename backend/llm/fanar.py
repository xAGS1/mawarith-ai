"""Fanar HTTP implementation. Only supplied messages; no external retrieval."""
import json
import os
import requests


def generate(messages, max_tokens, temperature, schema=None):
    from backend.llm.transport import ProviderError
    key=os.getenv('FANAR_API_KEY','').strip()
    if not key:
        raise ProviderError('LLM service unavailable')
    messages=[dict(m) for m in messages]
    if schema:
        messages[0]['content'] += '\nReturn strict JSON only, matching this schema:\n'+json.dumps(schema,ensure_ascii=False)
    model=os.getenv('FANAR_MODEL','Fanar-C-2-27B')
    response=requests.post(os.getenv('FANAR_BASE_URL','https://api.fanar.qa/v1').rstrip('/')+'/chat/completions',
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'},
        json={'model':model,'messages':messages,'max_tokens':max_tokens,'temperature':temperature,'stream':False},timeout=(10,90))
    if not response.ok:
        # Do not retain the credential-bearing requests exception/response.
        import logging
        logging.getLogger(__name__).warning('Fanar request failed status=%s',response.status_code)
        raise ProviderError('LLM service unavailable')
    data=response.json()
    return data['choices'][0]['message']['content'],data.get('model',model),data.get('usage') or {},response.status_code
