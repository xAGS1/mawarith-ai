"""Learning-only content integrity and presentation semantics."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContentItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: Any
    status: Literal["source_verbatim", "reviewed_summary", "draft"] = "draft"
    source_id: str | None = None
    reviewer: str | None = None
    reviewed_at: str | None = None

    @model_validator(mode="after")
    def validate_provenance(self):
        if self.status != "draft" and not self.source_id:
            raise ValueError("Verified content requires a source_id")
        if self.status == "reviewed_summary" and not (self.reviewer and self.reviewed_at):
            raise ValueError("Reviewed summaries require reviewer and reviewed_at")
        return self


class Definition(ContentItem):
    value: Any = Field(alias="text")


class StructuredConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title_ar: str
    title_en: str
    definition: Definition
    properties: dict[str, ContentItem] = Field(default_factory=dict)
    source_records: dict[str, dict] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_content(self):
        if self.definition.status != "draft" and not verified_item(self.definition.model_dump(), self.source_records):
            raise ValueError("Definition does not trace to approved evidence")
        for item in self.properties.values():
            if item.status != "draft" and not verified_item(item.model_dump(), self.source_records):
                raise ValueError("Property does not trace to approved evidence")
        return self


def verified_item(item: dict, sources: dict) -> bool:
    try:
        content = ContentItem.model_validate(item)
    except (ValueError, TypeError):
        return False
    if content.status == "draft":
        return False
    source = sources.get(content.source_id, {})
    if source.get("verified_source") is not True or not source.get("exact_text"):
        return False
    if content.status == "source_verbatim":
        values = content.value if isinstance(content.value, list) else [content.value]
        return bool(values) and all(isinstance(v, str) and bool(v.strip())
                                    and v in source["exact_text"] for v in values)
    return content.value is not None and content.value != ""


def verified_definition(concept: dict) -> bool:
    definition = concept.get("definition", {})
    return verified_item({"value": definition.get("text"), **{k: definition.get(k) for k in
        ("status", "source_id", "reviewer", "reviewed_at")}}, concept.get("source_records", {}))


def verified_properties(concept: dict) -> dict:
    return {name: item for name, item in concept.get("properties", {}).items()
            if verified_item(item, concept.get("source_records", {}))}


def render_value(item: dict, language: str) -> str:
    value = item["value"]
    if isinstance(value, dict):
        return value.get(language, "")
    if isinstance(value, list):
        return "، ".join(value) if language == "ar" else ", ".join(value)
    return str(value)
