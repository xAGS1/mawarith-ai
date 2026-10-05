"""Explicit learn/case dispatch, preserving the existing solver API."""
from backend.pipeline.learn_pipeline import run_learn, detect_language, collect_excerpts
from backend.pipeline.qwen_pipeline import run_pipeline as _run_case_pipeline
from backend.schemas.response import EducationalResponse, Concept
from backend.pipeline.understanding import understand, CURRENT_UNDERSTANDING, CURRENT_TRACE
from backend.pipeline.evidence_plan import build_evidence_plan, record_trace
from backend.pipeline.case_explanation import explain_case_question
from backend.pipeline.request_classifier import classify_request
from backend.pipeline.semantic_request import understand_request
from backend.pipeline.understanding import fallback_understanding
from backend.pipeline.rag_answer import answer_educational
from backend.schemas.response import EducationalResponse
from backend.llm import provider
from backend.pipeline.educational_claims import filter_claims, without_internal_ids, filter_calculation_prose
import json
import requests
import re


def run_pipeline(question, **kwargs):
    kwargs["deterministic"] = True
    return _run_case_pipeline(question, **kwargs)


def _public_response(value):
    if isinstance(value, dict):
        return {k: ([] if k == "fiqh_evidence" else _public_response(v)) for k, v in value.items()
            if k not in {"evidence_id", "chunk_id", "input_file", "repository_file", "local_source", "internal_provenance"}
            and "sha256" not in k and not k.startswith("excerpt_char_") and k not in {"char_start", "char_end"}}
    if isinstance(value, list):
        return [_public_response(v) for v in value]
    return value


def run_request(question: str, mode: str | None = None, *, debug_trace: dict | None = None, concept_context: dict | None = None) -> dict:
    # Optional page context affects educational understanding only, never case inputs.
    if concept_context is not None and mode == "learn":
        return _public_response(_answer_request(question, mode, debug_trace=debug_trace, concept_context=concept_context))
    return _public_response(_answer_request(question, mode, debug_trace=debug_trace))


def _answer_request(question: str, mode: str | None = None, *, debug_trace: dict | None = None, concept_context: dict | None = None) -> dict:
    if mode not in {None, "learn", "case"}:
        raise ValueError("mode must be learn or case")
    kwargs = {"concept_context": concept_context} if concept_context is not None else {}
    request = understand_request(question, mode, **kwargs) if question.strip() else None
    if request is None:
        # Compatibility fallback only when semantic understanding is unavailable.
        # No second understanding request is made.
        return _run_legacy_request(question, mode, debug_trace=debug_trace)
    if debug_trace is not None:
        debug_trace.update(understanding_origin="ai", semantic_request=request.model_dump(),
            detected_intent=request.intent, request_type=request.intent,
            mode_hint=mode, response_type=request.intent)
    if request.intent == "educational":
        return answer_educational(question, request, debug_trace, **kwargs)
    if request.intent in {"clarification_needed", "out_of_scope"} or request.case is None:
        clarification = request.intent != "out_of_scope"
        return EducationalResponse(mode="case" if request.case is not None or mode == "case" else "learn",
            language=request.language, decision_state="needs_clarification" if clarification else "out_of_scope",
            answer=request.clarification_question or ("يرجى توضيح سؤال المواريث." if request.language == "ar" else "Please clarify your inheritance question."),
            clarification_question=request.clarification_question if clarification else None).model_dump()
    case = run_pipeline(question, parsed_relations=request.case.parsed(), deterministic=True)
    response = _run_request(question, "case", case_result=case)
    if debug_trace is not None:
        debug_trace.update(parsed_entities=case["parsed_relations"], readiness_confirmation=case["case_readiness"],
            selected_rule_ids=[r["rule_id"] for r in case["sources"]], verified_result=case["result"])
    if response["decision_state"] == "ready":
        # Explanation transport cannot write back into the solver's result.
        evidence = [{"evidence_id": "E1", "text": json.dumps(case["result"], ensure_ascii=False),
                     "source_name": "Verified deterministic calculation"}]
        evidence.extend({"evidence_id": f"E{i+2}", "text": r["rule"], "source_name": r["source"]["source_name"]}
                        for i, r in enumerate(case["sources"]))
        try:
            generated = provider.explain_context(question, request.language, evidence, case["result"])
            answer, blocked = filter_claims(generated.get("answer", ""), evidence, generated.get("evidence_ids", []))
            answer = filter_calculation_prose(answer, case["result"])
            if generated.get("status") == "ready" and answer.strip():
                response["answer"] = without_internal_ids(answer)
            if debug_trace is not None:
                debug_trace.update(generated_explanation=generated, blocked_explanation_claims=blocked)
        except (requests.RequestException, ValueError, KeyError, TypeError):
            pass  # The verified distribution remains usable when prose fails.
    return response


def _run_legacy_request(question: str, mode: str | None = None, *, debug_trace: dict | None = None) -> dict:
    if mode not in {None, "learn", "case"}:
        raise ValueError("mode must be learn or case")
    understanding, origin = fallback_understanding(question), "deterministic_fallback"
    if mode is None:
        request_type, routing_origin = classify_request(question, understanding)
        mode = "case" if request_type == "calculation" else "learn"
    else:
        request_type = "calculation" if mode == "case" else "educational"
        routing_origin = "explicit_api_mode"
    if debug_trace is not None:
        debug_trace.update(request_type=request_type, routing_origin=routing_origin,
            response_type="calculation_result" if mode == "case" else "educational_explanation")
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


def _run_request(question: str, mode: str = "learn", *, case_result=None) -> dict:
    if mode == "learn":
        return run_learn(question)
    if mode != "case":
        raise ValueError("mode must be learn or case")
    language = detect_language(question)
    case = case_result if case_result is not None else run_pipeline(question)
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
