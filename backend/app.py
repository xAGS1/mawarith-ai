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
