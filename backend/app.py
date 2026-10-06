from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv


@asynccontextmanager
async def lifespan(app):
    # Uvicorn does not load .env unless --env-file is supplied. Preserve explicit
    # deployment environment values while loading local configuration at startup.
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    yield

from backend.pipeline.qwen_pipeline import run_pipeline
from backend.schemas.case import PipelineOutput

app = FastAPI(
    lifespan=lifespan,
    title="MAWARITH AI",
    version="0.1.0",
    description="Local Qwen parsing and reasoning with source retrieval and fraction verification."
)


class CaseRequest(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze-case", response_model=PipelineOutput)
def analyze_case_endpoint(payload: CaseRequest):
    try:
        result = run_pipeline(payload.question, deterministic=True)
        return PipelineOutput.model_validate(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


from typing import Literal
from backend.pipeline.educational_pipeline import run_request
from backend.schemas.response import EducationalResponse

class ConceptContext(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    slug: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=200)


class EducationalRequest(BaseModel):
    question: str
    mode: Literal["learn", "case"] = "learn"
    concept_context: ConceptContext | None = None

@app.post("/ask", response_model=EducationalResponse)
def ask_endpoint(payload: EducationalRequest):
    if payload.concept_context is not None and payload.mode == "learn":
        return run_request(payload.question, payload.mode,
            concept_context=payload.concept_context.model_dump())
    return run_request(payload.question, payload.mode)


from backend.learning.router import router as learning_router

app.include_router(learning_router)
