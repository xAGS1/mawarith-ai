"""Explicit learn/case dispatch, preserving the existing solver API."""
from backend.pipeline.learn_pipeline import run_learn, detect_language, collect_excerpts
from backend.pipeline.qwen_pipeline import run_pipeline
from backend.schemas.response import EducationalResponse, Concept
from backend.pipeline.understanding import understand, CURRENT_UNDERSTANDING, CURRENT_TRACE
from backend.pipeline.evidence_plan import build_evidence_plan, record_trace
from backend.pipeline.case_explanation import explain_case_question


def run_request(question: str, mode: str = "learn", *, debug_trace: dict | None = None) -> dict:
    if mode not in {"learn", "case"}:
        raise ValueError("mode must be learn or case")
    understanding, origin = understand(question)
    token = CURRENT_UNDERSTANDING.set(understanding)
    trace_token = CURRENT_TRACE.set(debug_trace)
    try:
        # The explicit API mode remains authoritative; intent is advisory.
        response = _run_request(question, mode)
        details = response.get("case_details") or {}
        plan = build_evidence_plan(details.get("sources", []) if mode == "case" else [],
                                   response.get("source_excerpts", []) if mode == "learn" else [])
        parsed = details.get("parsed_relations", {})
        record_trace(debug_trace, understanding, origin, plan, parsed)
        if debug_trace is not None:
            if mode == "learn" and response.get("evidence_status") == "supported":
                cited = {e.get("evidence_id") for e in response.get("source_excerpts", [])}
                debug_trace["explanation_claims"] = [c for c in debug_trace.get("planned_claims", plan)
                                                     if c["source_id"] in cited]
            debug_trace["deceased_gender"] = understanding.deceased_gender
            debug_trace["educational_question"] = understanding.educational_question
            debug_trace["readiness_confirmation"] = details.get("case_readiness", {})
        if (mode == "case" and understanding.intent == "mixed_case_and_question"
                and response.get("decision_state") == "ready"):
            explanation, claims, explanation_origin = explain_case_question(
                understanding.educational_question, understanding, plan)
            if explanation:
                response["answer"] += "\n\n" + explanation
            else:
                response["limitations"].append("No confirmed rule supports the attached educational question.")
            if debug_trace is not None:
                debug_trace.update(explanation_claims=claims, explanation_origin=explanation_origin)
        return response
    finally:
        CURRENT_UNDERSTANDING.reset(token)
        CURRENT_TRACE.reset(trace_token)


def _run_request(question: str, mode: str = "learn") -> dict:
    if mode == "learn":
        return run_learn(question)
    if mode != "case":
        raise ValueError("mode must be learn or case")
    language = detect_language(question)
    case = run_pipeline(question)
    ready = case["decision_state"] == "ready" and bool(case["result"] and
        case["result"].get("verification", {}).get("is_consistent"))
    decision_state = "ready" if ready else (case["decision_state"] if case["decision_state"] in {"needs_clarification", "out_of_scope"} else "specialist_referral")
    # Semantic similarity and neighboring chunks do not establish relevance to
    # a confirmed rule. For referrals, expose only rule-backed sources below.
    # Retain retrieval data in the internal pipeline result, not the public copy.
    public_case = {**case, "fiqh_evidence": []} if decision_state == "specialist_referral" else case
    if decision_state == "specialist_referral" and "fiqh_retrieval" in case:
        # Validation errors can embed raw payload text; keep those internal too.
        public_case["fiqh_retrieval"] = {"status": case["fiqh_retrieval"].get("status", "unavailable")}
    response = EducationalResponse(mode="case", language=language,
        decision_state=decision_state,
        answer=(("حُسبت الأنصبة باستخدام القواعد المتاحة وتحقق الحساب الكسري." if ready else
                 "لا تدعم القواعد المتاحة حل هذه المسألة كاملة. يرجى مراجعة مختص بالمواريث.") if language == "ar" else
                ("Shares were calculated using the available rules and checked with fraction arithmetic." if ready else
                 "The available rules do not support a complete solution. Consult an inheritance specialist.")),
        sources=case["sources"], source_excerpts=[] if decision_state == "specialist_referral" else collect_excerpts(case["fiqh_evidence"]),
        clarification_question=case.get("clarification_question"),
        case_details=public_case, limitations=["Arithmetic consistency does not establish legal completeness or correctness."])
    response.key_concepts = [Concept(term=r["topic"], explanation=r["rule"]) for r in case["sources"]]
    if response.decision_state == "needs_clarification":
        response.answer = "يلزم توضيح معلومات الأسرة قبل تطبيق قواعد المواريث." if language == "ar" else "The family information needs clarification before inheritance rules can be applied."
    elif response.decision_state == "out_of_scope":
        response.answer = "وضع المسائل مخصص لمسائل المواريث؛ يرجى ذكر حالة ميراث." if language == "ar" else "Case mode is for inheritance cases; please describe an inheritance case."
    if not ready:
        response.case_details = {**public_case, "result": None}
    displayed_sources = set()
    for rule in case["sources"]:
        source = rule.get("source", {})
        if source.get("arabic_text") and source.get("immutable_text"):
            identity = (source.get("source_type"), source["source_name"], source["reference"])
            if identity in displayed_sources:
                continue
            displayed_sources.add(identity)
            response.source_excerpts.append({"text": source["arabic_text"], "source_name": source["source_name"],
                "section": None, "reference": source["reference"], "source_url": source.get("source_url"), "immutable_text": True})
    return response.model_dump()
