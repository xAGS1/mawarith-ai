"""Explicit learn/case dispatch, preserving the existing solver API."""
from backend.pipeline.learn_pipeline import run_learn, detect_language, collect_excerpts
from backend.pipeline.qwen_pipeline import run_pipeline
from backend.schemas.response import EducationalResponse, Concept


def run_request(question: str, mode: str = "learn") -> dict:
    if mode == "learn":
        return run_learn(question)
    if mode != "case":
        raise ValueError("mode must be learn or case")
    language = detect_language(question)
    case = run_pipeline(question)
    ready = case["decision_state"] == "ready" and bool(case["result"] and
        case["result"].get("verification", {}).get("is_consistent"))
    response = EducationalResponse(mode="case", language=language,
        decision_state="ready" if ready else "specialist_referral",
        answer=(("حُسبت الأنصبة باستخدام القواعد المتاحة وتحقق الحساب الكسري." if ready else
                 "لا تدعم القواعد المتاحة حل هذه المسألة كاملة. يرجى مراجعة مختص بالمواريث.") if language == "ar" else
                ("Shares were calculated using the available rules and checked with fraction arithmetic." if ready else
                 "The available rules do not support a complete solution. Consult an inheritance specialist.")),
        sources=case["sources"], source_excerpts=collect_excerpts(case["fiqh_evidence"]),
        case_details=case, limitations=["Arithmetic consistency does not establish legal completeness or correctness."])
    if ready:
        response.key_concepts = [Concept(term=r["topic"], explanation=r["rule"]) for r in case["sources"]]
    if not ready:
        response.case_details = {**case, "result": None}
    for rule in case["sources"]:
        source = rule.get("source", {})
        if source.get("arabic_text") and source.get("immutable_text"):
            response.source_excerpts.append({"text": source["arabic_text"], "source_name": source["source_name"],
                "section": None, "reference": source["reference"], "source_url": source.get("source_url"), "immutable_text": True})
    return response.model_dump()
