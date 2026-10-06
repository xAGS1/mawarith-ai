"""One-attempt production parity check; preserves the original local baseline."""

import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse


def summarize(response, trace):
    case = response.get("case_details") or {}
    result = case.get("result") or {}
    sources = [*response.get("source_excerpts", []), *response.get("sources", []), *case.get("sources", [])]
    references, ids = [], set()
    for source in sources:
        meta = {**(source.get("provenance") or {}), **source, **(source.get("source") or {})}
        ref = meta.get("reference")
        if not ref:
            ref = {"volume": meta["volume"]} if meta.get("volume") else {"page": meta.get("page")}
        item = {"source_name": meta.get("source_name"), "reference": ref}
        if item not in references:
            references.append(item)
        if meta.get("source_id"):
            ids.add(meta["source_id"])
        elif meta.get("source_type") == "quran" and isinstance(ref, str):
            ids.add("quran:" + ref)
    for rule in result.get("rule_trace", []):
        ids.update(rule.get("source_ids", []))
    state = response.get("decision_state")
    return {"decision_state": state, "returned_mode": response.get("mode"),
            "evidence_status": response.get("evidence_status"),
            "parsed_heirs": (case.get("parsed_relations") or {}).get("mentioned_relatives", []),
            "final_fractions": (result.get("post_tasil") or {}).get("distribution", []),
            "verification": result.get("verification"), "source_ids": sorted(ids),
            "unique_source_references": references,
            "clarification_question": response.get("clarification_question"),
            "referral_reason": (case.get("case_readiness") or {}).get("reason") if state == "specialist_referral" else None,
            "answer_summary": response.get("answer"),
            "fiqh_retrieval_status": (case.get("fiqh_retrieval") or {}).get("status"),
            "answer_status": response.get("evidence_status") if response.get("mode") == "learn" else state,
            "explanation_error": trace.get("explanation_error")}


def normalized(field, value):
    if field == "final_fractions":
        return sorted((x["heir"], x["count"], str(Fraction(x["per_head_shares"]))) for x in (value or []))
    if field in ("unique_source_references", "source_ids", "retrieved_source_ids", "parsed_heirs"):
        return sorted(json.dumps(x, ensure_ascii=False, sort_keys=True) for x in (value or []))
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--baseline", type=Path, default=Path("evaluation/results/deployment_parity_baseline.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/results/deployment_parity_cloud.json"))
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv
        if not args.env_file.is_file():
            parser.error("Environment file not found")
        load_dotenv(args.env_file, override=False)
    missing = [k for k in ("QDRANT_HOST", "QDRANT_API_KEY", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_API_TOKEN", "FANAR_API_KEY") if not os.getenv(k)]
    if missing:
        parser.error("Missing environment variables: " + ", ".join(missing))
    if os.getenv("EMBEDDING_PROVIDER", "local").strip().lower() != "cloudflare" or os.getenv("LLM_PROVIDER", "ollama").strip().lower() != "fanar":
        parser.error("This check requires EMBEDDING_PROVIDER=cloudflare and LLM_PROVIDER=fanar")
    host = urlparse(os.environ["QDRANT_HOST"])
    if host.scheme != "https" or not host.hostname or not host.hostname.endswith(".cloud.qdrant.io"):
        parser.error("QDRANT_HOST must identify the HTTPS Qdrant Cloud endpoint")
    if args.output.resolve() == args.baseline.resolve() or args.output.exists():
        parser.error("Output must be new and must not overwrite the baseline")
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))["records"]
    if len(baseline) != 12 or [r["number"] for r in baseline] != list(range(1, 13)):
        parser.error("Expected the existing numbered 12-question baseline")
    from backend.pipeline.educational_pipeline import run_request
    from backend.llm.transport import LAST_GENERATION
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "attempts_per_question": 1,
              "embedding_provider": "cloudflare", "configured_provider": "fanar", "records": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def save():
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    save()
    for old in baseline:
        trace = {}
        record = {"number": old["number"], "mode": old["mode"], "question": old["question"]}
        started = perf_counter()
        LAST_GENERATION.set(None)
        try:
            response = run_request(old["question"], old["mode"], debug_trace=trace)
            record.update(summarize(response, trace), request_success=True, response=response)
        except Exception as exc:
            record.update(request_success=False, error_type=type(exc).__name__)
        record["latency_seconds"] = round(perf_counter() - started, 3)
        record["generation_telemetry"] = LAST_GENERATION.get()
        fields = ("request_success", "decision_state", "returned_mode", "evidence_status", "final_fractions", "verification",
                  "source_ids", "unique_source_references", "clarification_question", "referral_reason", "answer_summary", "parsed_heirs")
        record["differences"] = {f: {"baseline": old.get(f), "current": record.get(f)} for f in fields
                                 if normalized(f, old.get(f)) != normalized(f, record.get(f))}
        old_retrieval = ((old.get("response") or {}).get("case_details") or {}).get("fiqh_retrieval") or {}
        if old_retrieval.get("status") != record.get("fiqh_retrieval_status"):
            record["differences"]["fiqh_retrieval_status"] = {"baseline": old_retrieval.get("status"), "current": record.get("fiqh_retrieval_status")}
        record["latency_delta_seconds"] = round(record["latency_seconds"] - old["latency_seconds"], 3)
        report["records"].append(record)
        save()
        print(json.dumps({k: record.get(k) for k in ("number", "question", "decision_state", "final_fractions", "source_ids",
            "unique_source_references", "clarification_question", "referral_reason", "answer_status", "fiqh_retrieval_status", "latency_seconds", "latency_delta_seconds", "differences", "error_type")}, ensure_ascii=False, indent=2), flush=True)
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    save()
    print("# | baseline -> current | latency | changed fields")
    for old, new in zip(baseline, report["records"]):
        print(f"{new['number']} | {old['decision_state']} -> {new.get('decision_state', 'FAILED')} | {new['latency_seconds']}s | {', '.join(new['differences']) or 'none'}")
    return int(any(not r["request_success"] for r in report["records"]))


if __name__ == "__main__":
    raise SystemExit(main())
