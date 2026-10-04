from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HeirItem(BaseModel):
    heir: str
    count: int = Field(ge=1)


class ShareItem(BaseModel):
    heir: str
    count: int = Field(ge=1)
    fraction: str = Field(description="Group share of the whole estate, including all count individuals")


class DistributionItem(BaseModel):
    heir: str
    count: int = Field(ge=1)
    per_head_shares: str = Field(description="Share of the whole estate for one individual")
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


class SourceCoverage(BaseModel):
    is_sufficient: bool
    covered_relations: List[str]
    unsupported_relations: List[str]
    coverage_ratio: float = Field(ge=0, le=1)


class PipelineOutput(BaseModel):
    question: str
    parsed_relations: dict
    case_features: dict
    sources: List[dict]
    fiqh_evidence: List[dict]
    fiqh_retrieval: dict
    source_coverage: SourceCoverage
    decision_state: Literal["ready", "needs_clarification", "specialist_referral", "out_of_scope"]
    clarification_question: Optional[str] = None
    case_readiness: dict = Field(default_factory=dict)
    result: Optional[InheritanceOutput]
