from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.pipeline.qwen_pipeline import run_pipeline
from backend.schemas.case import PipelineOutput

app = FastAPI(
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
        result = run_pipeline(payload.question)
        return PipelineOutput.model_validate(result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


from typing import Literal
from backend.pipeline.educational_pipeline import run_request
from backend.schemas.response import EducationalResponse

class EducationalRequest(BaseModel):
    question: str
    mode: Literal["learn", "case"] = "learn"

@app.post("/ask", response_model=EducationalResponse)
def ask_endpoint(payload: EducationalRequest):
    return run_request(payload.question, payload.mode)


from backend.learning.router import router as learning_router

app.include_router(learning_router)
