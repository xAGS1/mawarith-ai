"""Environment-selected generation transport. No retrieval or religious logic."""
import json
import logging
import os
import time
from contextvars import ContextVar
import requests

LAST_GENERATION = ContextVar('last_llm_generation', default=None)
logger = logging.getLogger(__name__)

class ProviderError(requests.RequestException):
    """Safe provider failure; never retains request/response credentials."""


def selected_provider():
    value = os.getenv('LLM_PROVIDER', 'ollama').lower()
    if value == 'qwen':  # Backward compatibility for existing local installations.
        value = 'ollama'
    if value not in {'fanar', 'ollama'}:
        raise ProviderError('LLM service unavailable')
    return value


def generate(messages, max_tokens=600, temperature=0, response_format=None, *, provider=None):
    LAST_GENERATION.set(None)
    name = provider or selected_provider()
    started = time.perf_counter()
    status = None
    try:
        if name == 'fanar':
            from backend.llm.fanar import generate as fanar_generate
            answer, model, usage, status = fanar_generate(messages, max_tokens, temperature, response_format)
        elif name == 'ollama':
            model = os.getenv('OLLAMA_MODEL', 'qwen3:8b')
            r = requests.post(os.getenv('OLLAMA_HOST', 'http://127.0.0.1:11434').rstrip('/')+'/api/chat',
                json={'model':model, 'messages':messages, 'stream':False, 'think':False,
                      **({'format':response_format} if response_format else {}),
                      'options':{'temperature':temperature, 'num_predict':max_tokens, 'num_ctx':8192}}, timeout=(10,90))
            status=r.status_code
            if not r.ok:
                raise ProviderError('LLM service unavailable')
            data=r.json()
            answer=data['message']['content']
            usage={'prompt_tokens':data.get('prompt_eval_count'), 'completion_tokens':data.get('eval_count')}
        else:
            raise ProviderError('LLM service unavailable')
        if not isinstance(answer,str) or not answer.strip():
            raise ProviderError('LLM service unavailable')
        if response_format:
            # Existing task-specific Pydantic/schema validation remains authoritative.
            parsed=json.loads(answer)
            if not isinstance(parsed,dict):
                raise ProviderError('LLM service unavailable')
        LAST_GENERATION.set({'provider':name,'model':model,'latency_seconds':time.perf_counter()-started,**usage})
        return answer
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError):
        logger.warning('LLM generation failed provider=%s status=%s latency=%.3f',name,status,time.perf_counter()-started)
        if name == 'fanar' and os.getenv('LLM_FALLBACK_PROVIDER','none').lower() == 'ollama':
            return generate(messages,max_tokens,temperature,response_format,provider='ollama')
        raise ProviderError('LLM service temporarily unavailable') from None


class GenerationResponse:
    """Compatibility envelope for existing strict structured task adapters."""
    def __init__(self,text): self.text=text
    def raise_for_status(self): pass
    def json(self): return {'response':self.text}


def fanar_ollama_payload(payload):
    messages=[{'role':'system','content':payload.get('system','')},
              {'role':'user','content':payload.get('prompt','')}]
    options=payload.get('options',{})
    return GenerationResponse(generate(messages, options.get('num_predict',600),
        options.get('temperature',0),payload.get('format')))
