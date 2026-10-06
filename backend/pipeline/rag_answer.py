"""General educational answering; no curated concept or definition branches."""
import requests
import re
from backend.llm import provider
from backend.rag.educational_context import retrieve_context
from backend.schemas.response import EducationalResponse
from backend.pipeline.educational_claims import filter_claims, without_internal_ids
from backend.pipeline.educational_grounding import check_concept_scope
from backend.pipeline.educational_sentence_check import check_sentences, check_consistency
from backend.pipeline.fanar_sentence_check import check_cited_support
from backend.llm.transport import selected_provider, LAST_GENERATION


def answer_educational(question, request, trace=None, *, concept_context=None):
    response = EducationalResponse(mode="learn", language=request.language,
        decision_state="out_of_scope", evidence_status="insufficient",
        answer="لا تكفي الأدلة المتاحة لتقديم شرح موثق لهذا السؤال." if request.language == "ar" else
               "The available evidence is insufficient for a sourced explanation.")
    if concept_context is not None:
        # A soft query hint, not a source/concept filter. The original question and
        # the understanding layer's other search terms are always retained.
        request = request.model_copy(update={"retrieval_query": request.retrieval_query +
            "\n" + concept_context["title"]})
    evidence = retrieve_context(question, request, trace)
    if trace is not None:
        trace["educational_evidence"] = evidence
    if not evidence:
        response.limitations.append("لم تتوفر أدلة معتمدة ذات صلة." if request.language == "ar" else "No relevant approved evidence was available.")
        return response.model_dump()
    prompt_evidence = [{k: e.get(k) for k in ("evidence_id", "text", "source_name", "section", "page", "source_type")} for e in evidence]
    try:
        explanation_question = question
        if concept_context is not None:
            import json
            explanation_question = json.dumps({"question": question,
                "current_concept": concept_context,
                "context_policy": "Page context only, not evidence. Resolve references; answer only from the supplied evidence."}, ensure_ascii=False)
        LAST_GENERATION.set(None)
        generated = provider.explain_context(explanation_question, request.language, prompt_evidence)
        generation_provider = (LAST_GENERATION.get() or {}).get("provider", selected_provider())
        if trace is not None:
            trace["generated_explanation"] = generated
        if generated.get("status") != "ready" or not isinstance(generated.get("answer"), str):
            return response.model_dump()
        declared = generated.get("evidence_ids", [])
        if not isinstance(declared, list) or any(not isinstance(i, str) for i in declared):
            raise ValueError("Invalid declared citation IDs")
        answer, inconsistent = check_consistency(generated["answer"])
        screen = check_cited_support if generation_provider == "fanar" else check_sentences
        answer, uncertain = screen(answer, evidence, declared)
        if trace is not None:
            trace["sentence_screen_policy"] = "fanar_hard_checks" if generation_provider == "fanar" else "qwen_strict_lexical"
            trace["consistency_removals"] = inconsistent
            trace["sentence_screen_removals"] = uncertain
            trace["after_sentence_screen"] = answer
        answer, blocked = filter_claims(answer, evidence, declared)
        if trace is not None:
            trace["claim_guard_removals"] = blocked
            trace["after_claim_guard"] = answer
        blocked = inconsistent + uncertain + blocked
        if trace is not None:
            trace["blocked_explanation_claims"] = blocked
        if not answer.strip():
            return response.model_dump()
        ids = set(re.findall(r"\[(E\d+)\]", answer)) or set(declared)
        selected = [e for e in evidence if e["evidence_id"] in ids]
        check_concept_scope(question, answer, selected)
        response.answer = without_internal_ids(answer)
        response.decision_state = "ready"
        response.evidence_status = "supported"
        seen = set()
        for e in selected:
            source = e["provenance"]
            identity = (source.get("source_id"), source.get("source_name"), source.get("reference"), source.get("volume"))
            if identity not in seen:
                seen.add(identity)
                response.sources.append(source)
        response.source_excerpts = [{k: v for k, v in e.items() if k not in {"evidence_id", "internal_provenance"}} for e in selected[:2]]
        if blocked:
            response.limitations.append("حُذفت عبارات لم تدعمها الأدلة المرفقة." if request.language == "ar" else "Statements unsupported by the cited evidence were omitted.")
    except (requests.RequestException, ValueError, KeyError, TypeError) as exc:
        if trace is not None:
            trace["explanation_error"] = type(exc).__name__
        response.limitations.append("تعذر إكمال الشرح الموثق." if request.language == "ar" else "The grounded explanation could not be completed.")
    return response.model_dump()
