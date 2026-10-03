"""Provenance validation for the initial approved source."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StrictBool, StrictInt, field_validator, model_validator


SOURCE_NAME = "الموسوعة الفقهية الكويتية"
PUBLISHER = "وزارة الأوقاف والشؤون الإسلامية - الكويت"


class FiqhSourceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_type: Literal["fiqh"]
    source_name: Literal["الموسوعة الفقهية الكويتية"]
    publisher: Literal["وزارة الأوقاف والشؤون الإسلامية - الكويت"]
    topic: str
    volume: StrictInt | None = Field(ge=1)
    page: StrictInt | None = Field(ge=1)
    section: str | None
    text: str
    source_url: HttpUrl
    verified_source: StrictBool

    @field_validator("verified_source")
    @classmethod
    def require_approval(cls, value):
        if value is not True:
            raise ValueError("Only locally approved sources may be ingested")
        return value

    @field_validator("topic", "text")
    @classmethod
    def require_text(cls, value):
        if not value.strip():
            raise ValueError("Source text and topic cannot be empty")
        return value  # Validate without trimming or normalizing source content.


class FiqhChunk(FiqhSourceRecord):
    chunk_id: str
    document_sha256: str
    input_file: str
    char_start: StrictInt = Field(ge=0)
    char_end: StrictInt = Field(gt=0)

    @model_validator(mode="after")
    def validate_offsets(self):
        if self.char_end - self.char_start != len(self.text):
            raise ValueError("Chunk offsets must match the exact text length")
        if len(self.document_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.document_sha256):
            raise ValueError("Invalid source document checksum")
        return self

    @field_validator("chunk_id", "document_sha256", "input_file")
    @classmethod
    def require_provenance(cls, value):
        if not value.strip():
            raise ValueError("Chunk identity and provenance are required")
        return value
