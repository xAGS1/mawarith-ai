"""Shared educational and case response contract."""
from typing import Literal
from pydantic import BaseModel, Field

class Concept(BaseModel):
    term: str
    explanation: str

class EducationalResponse(BaseModel):
    mode: Literal["learn", "case"]
    decision_state: Literal["ready", "needs_clarification", "specialist_referral", "out_of_scope"]
    language: Literal["ar", "en"]
    answer: str
    key_concepts: list[Concept] = Field(default_factory=list)
    source_excerpts: list[dict] = Field(default_factory=list)
    sources: list[dict] = Field(default_factory=list)
    clarification_question: str | None = None
    limitations: list[str] = Field(default_factory=list)
    case_details: dict | None = None
