"""Rebuild only UQU locally; optionally synchronize its isolated Qdrant collection.

python -m backend.rag.rebuild_uqu --index
"""
import argparse
import json
import os
from pathlib import Path
import uuid

import requests
from backend.learning.definition_retrieval import UQU_DIR, UQU_METADATA
from backend.rag.educational_context import source_windows
from backend.rag.fiqh.embeddings import DIMENSION, embed_texts, embedding_model_name
from backend.rag.uqu_extraction import write_corpus

COLLECTION = 'mawarith_uqu'
SOURCE_ID = 'uqu_mawarith_1'


def index_uqu(records, host=None):
    """Upsert validated replacements before pruning stale UQU points only."""
    if not records or any(r['source'].get('source_id') != SOURCE_ID or
                          r['source'].get('verified_source') is not True or
                          r['source'].get('retrieval_eligible') is False for r in records):
        raise ValueError('Only approved nonempty UQU records can be indexed')
    vectors = embed_texts([r['text'] for r in records])
    points = []
    for record, vector in zip(records, vectors, strict=True):
        source = record['source']
        key = f"{SOURCE_ID}:{source['chunk_id']}:{source['char_start']}:{source['excerpt_sha256']}"
        points.append({'id': str(uuid.uuid5(uuid.NAMESPACE_URL, key)), 'vector': vector,
                       'payload': {**record, 'source_id': SOURCE_ID, 'embedding_model': embedding_model_name()}})
    base = (host or os.getenv('QDRANT_HOST', 'http://localhost:6333')).rstrip('/')

    def call(method, suffix, body=None):
        response = requests.request(method, base + suffix, json=body, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get('status') != 'ok':
            raise RuntimeError('Qdrant UQU synchronization failed')
        return data['result']

    collections = call('GET', '/collections')['collections']
    root = f'/collections/{COLLECTION}'
    if not any(c['name'] == COLLECTION for c in collections):
        call('PUT', root, {'vectors': {'size': DIMENSION, 'distance': 'Cosine'}})
    else:
        params = call('GET', root)['config']['params']['vectors']
        if params['size'] != DIMENSION or params['distance'] != 'Cosine':
            raise ValueError('Existing UQU collection has an incompatible vector schema')
    for start in range(0, len(points), 32):
        call('PUT', root + '/points?wait=true', {'points': points[start:start + 32]})
    ids = [p['id'] for p in points]
    # Confirm all new IDs are persisted before any deletion.
    persisted = call('POST', root + '/points', {'ids': ids, 'with_payload': False, 'with_vector': False})
    if {p['id'] for p in persisted} != set(ids):
        raise RuntimeError('Incomplete UQU upsert; stale records have not been deleted')
    call('POST', root + '/points/delete?wait=true', {'filter': {
        'must': [{'key': 'source_id', 'match': {'value': SOURCE_ID}}],
        'must_not': [{'has_id': ids}]}})
    return call('POST', root + '/points/count', {'exact': True, 'filter': {
        'must': [{'key': 'source_id', 'match': {'value': SOURCE_ID}}]}})['count']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', action='store_true')
    args = parser.parse_args()
    output = UQU_DIR.parent / 'processed'
    pages = write_corpus(UQU_DIR / 'mawarith_course-uqu.pdf', UQU_METADATA, output / 'pages.json')
    chunks = source_windows(pages)
    (output / 'chunks.json').write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding='utf-8')
    count = index_uqu(chunks) if args.index else None
    print(json.dumps({'pages': len(pages), 'chunks': len(chunks), 'collection': COLLECTION,
                      'indexed_uqu_points': count}, ensure_ascii=False))


if __name__ == '__main__':
    main()
