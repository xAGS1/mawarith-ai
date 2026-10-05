"""Live educational demo check; source-bearing transcripts remain git-ignored."""
import json
import os
from pathlib import Path
import sys
import requests
import argparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')
from backend.pipeline.educational_pipeline import run_request
from backend.pipeline.rag_answer import answer_educational
from backend.pipeline.semantic_request import SemanticRequest
from backend.llm import provider

QUESTIONS = ['ما معنى أصحاب الفروض؟','ما معنى العصبة؟','ما الفرق بين الفرض والتعصيب؟',
             'ما معنى الحجب؟','ايش هي العول؟','ما معنى الرد؟',
             'فهمني العصبة ببساطة','ليش يصير العول؟','كيف الحجب يأثر على الورثة؟','وش يعني الرد؟']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recheck', action='store_true', help='Replay deterministic checks against actual saved live generations and current real retrieval')
    args = parser.parse_args()
    output = ROOT / 'data/fiqh/dorar_inheritance/processed/educational_demo.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    records = []
    previous = json.loads(output.read_text(encoding='utf-8')) if args.recheck else []
    if args.recheck and not output.with_name('educational_demo_live.json').exists():
        output.with_name('educational_demo_live.json').write_text(output.read_text(encoding='utf-8'), encoding='utf-8')
    original_post = requests.post
    metrics = []
    def measured_post(*args, **kwargs):
        response = original_post(*args, **kwargs)
        if str(args[0]).endswith('/api/generate') and response.ok:
            data = response.json()
            metrics.append({k:data.get(k) for k in ('prompt_eval_count','eval_count','done_reason')})
        return response
    requests.post = measured_post
    for question in QUESTIONS:
        metrics.clear()
        trace = {}
        if args.recheck:
            saved = next(r for r in previous if r['question']==question)
            original_explain = provider.explain_context
            provider.explain_context = lambda *a: saved['trace'].get('generated_explanation', {'status':'insufficient_evidence'})
            try:
                response = answer_educational(question, SemanticRequest.model_validate(saved['trace']['semantic_request']), trace)
            finally:
                provider.explain_context = original_explain
            trace['semantic_request'] = saved['trace']['semantic_request']
            records.append({**saved,'response':response,'trace':trace,'postcheck_replayed':True})
        else:
            response = run_request(question, debug_trace=trace)
            records.append({'question':question,'response':response,'trace':trace,'generation_metrics':list(metrics)})
        output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        print(question, response.get('evidence_status'), response['answer'], flush=True)
    requests.post = original_post


if __name__ == '__main__':
    main()
