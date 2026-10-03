from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HeirItem(BaseModel):
    heir: str
    count: int = Field(ge=1)


class ShareItem(BaseModel):
    heir: str
    count: int = Field(ge=1)
    fraction: str


class DistributionItem(BaseModel):
    heir: str
    count: int = Field(ge=1)
    per_head_shares: str
    per_head_percent: Optional[float] = None


class PostTasil(BaseModel):
    total_shares: Optional[int] = None
    distribution: List[DistributionItem] = []


class FractionVerification(BaseModel):
    total_fraction: str
    is_consistent: bool


class InheritanceOutput(BaseModel):
    heirs: List[HeirItem] = []
    blocked: List[HeirItem] = []
    shares: List[ShareItem] = []
    awl_or_radd: str = "none"
    post_tasil: PostTasil = PostTasil()
    verification: Optional[FractionVerification] = None


class PipelineOutput(BaseModel):
    question: str
    parsed_relations: dict
    sources: List[dict]
    result: InheritanceOutput
