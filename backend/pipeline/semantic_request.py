"""One strict semantic understanding call; no answer or share generation."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
import requests
from backend.llm import qwen_understanding
from backend.rules.case_features import COUNT_RELATIONS
from backend.rules.educational_concepts import matching_text
import re


def canonical_relationship(relation):
    # Linguistic normalization only; never shorten chains or infer sibling type.
    key = re.sub(r"\bال", "", matching_text(relation))
    vocabulary = set(COUNT_RELATIONS.values()) | {"أخ", "أخت", "جد", "جدة"}
    return next((r for r in vocabulary if matching_text(r) == key), relation.strip())


class ExtractedHeir(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    relation: str = Field(min_length=1, max_length=150)
    count: int = Field(ge=1, le=100)


class CaseFacts(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    heirs: list[ExtractedHeir] = Field(max_length=30)
    relationships: list[str] = Field(max_length=30)
    counts: dict[str, int]

    @model_validator(mode="after")
    def consistent_counts(self):
        extracted = {}
        for heir in self.heirs:
            heir.relation = canonical_relationship(heir.relation)
            if heir.relation in extracted:
                raise ValueError("Duplicate relationship; aggregate stated counts")
            extracted[heir.relation] = heir.count
        self.relationships = [canonical_relationship(r) for r in self.relationships]
        self.counts = {canonical_relationship(r): n for r,n in self.counts.items()}
        if set(self.relationships) != set(extracted):
            raise ValueError("Each stated heir needs one canonical relationship and count")
        if any(r not in extracted or type(n) is not int or n != extracted[r] for r,n in self.counts.items()):
            raise ValueError("Counts disagree with extracted heirs")
        # counts is a derived index of the strict relation/count records, never
        # a guessed default for a missing person or unknown number.
        self.counts = extracted
        return self

    def parsed(self):
        return {"mentioned_relatives": [{"relation": h.relation, "count": h.count} for h in self.heirs]}


class SemanticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    intent: Literal["educational", "calculation", "clarification_needed", "out_of_scope"]
    language: Literal["ar", "en"]
    topic: str = Field(max_length=300)
    retrieval_query: str = Field(max_length=1000)
    concepts: list[str] = Field(max_length=5)
    case: CaseFacts | None
    clarification_question: str | None = Field(max_length=500)


def understand_request(question, mode_hint=None, *, concept_context=None):
    try:
        # The current frontend always sends a legacy mode. Supplying it to the
        # semantic model biased concrete cases into educational distributions.
        # Keep it only for service-failure compatibility, not understanding.
        kwargs = {"concept_context": concept_context} if concept_context is not None else {}
        payload = qwen_understanding.understand_input(question, SemanticRequest.model_json_schema(), **kwargs)
        return SemanticRequest.model_validate(payload)
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None
