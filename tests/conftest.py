"""Never let locally installed real source text affect synthetic unit tests."""

import pytest


@pytest.fixture(autouse=True)
def isolate_runtime_fiqh_corpus(tmp_path, monkeypatch):
    from backend.rag.fiqh import vector_store
    monkeypatch.setattr(vector_store, "DATA_DIR", tmp_path / "empty-fiqh-corpus")
