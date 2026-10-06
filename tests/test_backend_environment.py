import asyncio
from dotenv import load_dotenv as actual_load
from backend import app as api
from backend.llm.transport import selected_provider


def test_backend_startup_loads_local_provider_env(monkeypatch,tmp_path):
    env=tmp_path/'settings.env'
    env.write_text('LLM_PROVIDER=fanar\nLLM_FALLBACK_PROVIDER=none\n',encoding='utf8')
    monkeypatch.delenv('LLM_PROVIDER',raising=False)
    monkeypatch.delenv('LLM_FALLBACK_PROVIDER',raising=False)
    seen=[]
    def load(path,override):
        seen.append((path,override))
        return actual_load(env,override=override)
    monkeypatch.setattr(api,'load_dotenv',load)
    async def startup():
        async with api.lifespan(api.app):
            assert selected_provider()=='fanar'
    asyncio.run(startup())
    assert seen[0][0].name=='.env'
    assert seen[0][1] is False


def test_backend_startup_preserves_explicit_provider(monkeypatch,tmp_path):
    env=tmp_path/'settings.env'
    env.write_text('LLM_PROVIDER=fanar\n',encoding='utf8')
    monkeypatch.setenv('LLM_PROVIDER','ollama')
    monkeypatch.setattr(api,'load_dotenv',lambda path,override:actual_load(env,override=override))
    async def startup():
        async with api.lifespan(api.app):
            assert selected_provider()=='ollama'
    asyncio.run(startup())
