"""Select the educational LLM provider; currently only local Qwen is supported."""
import os

from backend.llm import qwen_explainer


def explain(question: str, language: str, evidence: list[dict]) -> dict:
    provider = os.getenv("LLM_PROVIDER", "qwen")
    if provider != "qwen":
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
    return qwen_explainer.explain(question, language, evidence)
