"""Reproducible local retrieval/answer audit; full source-bearing output stays ignored."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

from backend.pipeline.educational_pipeline import run_request
from backend.pipeline.semantic_request import SemanticRequest
from backend.rag.educational_context import retrieve_context
from backend.rag.dorar_retrieval import dorar_candidates
from backend.rag.dorar_ingestion import DATA_DIR


def main():
    questions = ['من هم أصحاب الفروض؟','ايش معنى الفرض؟','فهمني العصبة','وش هو التعصيب؟',
                 'كيف يعمل الحجب؟','ايش هي العول؟','وش يعني الرد؟']
    records = []
    output = DATA_DIR / 'processed/live_validation.json'
    for question in questions:
        trace = {}
        response = run_request(question, debug_trace=trace)
        request = SemanticRequest.model_validate(trace['semantic_request']) if trace.get('semantic_request') else None
        evidence = retrieve_context(question, request) if request else []
        records.append({'question':question,'top_retrieved_chunks':evidence,
                        'top_dorar_chunks':dorar_candidates(question,question),
                        'response':response,'trace':trace,
                        'unsupported_claim_status':{'guard_blocked':trace.get('blocked_explanation_claims',[]),
                                                    'manual_review':'pending'}})
        output.write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        print(question, response.get('evidence_status'), response['answer'], flush=True)


if __name__=='__main__':
    main()
