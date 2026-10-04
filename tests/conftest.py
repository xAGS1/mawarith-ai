"""Never let locally installed real source text affect synthetic unit tests."""

import pytest
import requests


@pytest.fixture(autouse=True)
def isolate_new_understanding_transport(monkeypatch):
    """Existing regressions must not make additional live classifier calls."""
    from backend.llm import qwen_understanding
    from unittest.mock import Mock
    monkeypatch.setattr(qwen_understanding, "understand_input", Mock(side_effect=requests.ConnectionError("Offline test")))
    monkeypatch.setattr(qwen_understanding, "select_claims", Mock(side_effect=requests.ConnectionError("Offline test")))


@pytest.fixture(autouse=True)
def isolate_runtime_fiqh_corpus(tmp_path, monkeypatch):
    from backend.rag.fiqh import vector_store
    monkeypatch.setattr(vector_store, "DATA_DIR", tmp_path / "empty-fiqh-corpus")
