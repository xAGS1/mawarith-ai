"""Manual, live production smoke check after rebuilding the local UQU corpus."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TRANSFORMERS_OFFLINE', '1')

from backend.pipeline.educational_pipeline import run_request


def main():
    questions = ['ايش هي العول؟', 'ما معنى العصبة؟', 'وش يعني الرد؟', 'فهمني الحجب', 'ما معنى الفرض؟']
    output = ROOT / 'evaluation/uqu_extraction_live.json'
    records = []
    for question in questions:
        trace = {}
        response = run_request(question, debug_trace=trace)
        records.append({'question': question, 'response': response, 'trace': trace})
        output.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
        print(question, response['evidence_status'], response['answer'], flush=True)


if __name__ == '__main__':
    main()
