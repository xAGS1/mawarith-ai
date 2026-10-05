"""Source-scoped Dorar vectors in the existing fiqh retrieval collection."""
import hashlib
import json
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

from backend.rag.dorar_ingestion import DATA_DIR, SOURCE_ID, matching
from backend.rag.fiqh.embeddings import embed_texts, embedding_model_name, DIMENSION
from backend.rag.fiqh.vector_store import QdrantFiqhStore


def load_dorar_chunks():
    path = DATA_DIR / 'processed/chunks.json'
    if not path.exists():
        return []
    chunks = json.loads(path.read_text(encoding='utf-8'))
    result = []
    for chunk in chunks:
        source = chunk['source']
        if source.get('source_id') != SOURCE_ID or source.get('book') != 'كتاب المواريث':
            raise ValueError('Dorar corpus is not inheritance-only')
        text = chunk['exact_text']
        if hashlib.sha256(text.encode()).hexdigest() != source['excerpt_sha256'] or chunk['text'] != text:
            raise ValueError('Dorar exact source text hash mismatch')
        if source.get('retrieval_eligible') is True and source.get('verified_source') is True:
            result.append(chunk)
    return result


def index_dorar():
    chunks = load_dorar_chunks()
    if not chunks:
        raise ValueError('No eligible Dorar chunks; existing vectors will not be changed')
    store = QdrantFiqhStore()
    store.ensure_collection(create=False)
    info = store._request('GET', f'/collections/{store.collection}')
    vectors_config = info['config']['params']['vectors']
    if vectors_config['size'] != DIMENSION or vectors_config['distance'] != 'Cosine':
        raise ValueError('Existing educational collection is incompatible')
    vectors = embed_texts([c['text'] for c in chunks])
    points = [{'id': str(uuid5(NAMESPACE_URL, SOURCE_ID + ':' + c['source']['chunk_id'])),
               'vector': v, 'payload': {**c, **c['source'], 'embedding_model': embedding_model_name()}}
              for c, v in zip(chunks, vectors, strict=True)]
    base = f'/collections/{store.collection}/points'
    for start in range(0, len(points), 32):
        store._request('PUT', base + '?wait=true', {'points': points[start:start+32]})
    ids = [p['id'] for p in points]
    persisted = store._request('POST', base, {'ids': ids, 'with_payload': False, 'with_vector': False})
    if {p['id'] for p in persisted} != set(ids):
        raise RuntimeError('Dorar indexing incomplete; no old records deleted')
    # Only this source can be pruned, and only after replacement verification.
    store._request('POST', base + '/delete?wait=true', {'filter': {
        'must': [{'key':'source_id','match':{'value':SOURCE_ID}}], 'must_not':[{'has_id': ids}]}})
    return store._request('POST', base + '/count', {'exact': True, 'filter': {
        'must':[{'key':'source_id','match':{'value':SOURCE_ID}}]}})['count']


def retrieval_style(question):
    """General presentation intent, not a concept/page routing table."""
    import re
    text = matching(question)
    if re.search(r'مثال|مثالا|امثلة', text):
        return 'example'
    if re.search(r'ما معنى|ايش معنى|وش يعني|وش هو|من هم|ما المقصود|تعريف|عرف|ايش هي', text):
        return 'definition'
    return 'explanation'


def ranking_score(question, record):
    import re
    source = record['source']
    style = retrieval_style(question)
    kind = source.get('content_kind')
    bonus = .03 if source.get('source_type') == 'educational_reference' else .015 if source.get('source_type') == 'fiqh_reference' else 0
    if source.get('extraction_quality') == 'clean_html':
        bonus += .015
    preferred = {'definition': {'definition'}, 'explanation': {'definition','explanation','rule'},
                 'example': {'example','rule','condition'}}[style]
    if kind in preferred:
        bonus += .045
    # Match topic words despite punctuation/diacritics; generic instructional
    # words must not promote an introductory article over the actual topic.
    stopwords = {'معنى','تعريف','عرف','اشرح','فهمني','يعني','ايش','كيف','يعمل','علم','المواريث','الفرائض'}
    terms = {t for t in re.findall(r'[\u0621-\u064a]+', matching(question)) if len(t)>2 and t not in stopwords}
    topics = set(re.findall(r'[\u0621-\u064a]+', matching(source.get('topic') or source.get('section') or '')))
    bonus += .04 * min(2, len(terms & topics))
    return record.get('score', 0) + bonus


def dorar_candidates(question, query, top_k=3):
    approved = {c['source']['chunk_id']: c for c in load_dorar_chunks()}
    if not approved:
        return []
    store = QdrantFiqhStore()
    vector = embed_texts([query])[0]
    response = store._request('POST', f'/collections/{store.collection}/points/query', {
        'query':vector, 'limit':max(top_k, 8), 'with_payload':True,
        'filter':{'must':[{'key':'source_id','match':{'value':SOURCE_ID}},
                          {'key':'verified_source','match':{'value':True}},
                          {'key':'embedding_model','match':{'value':embedding_model_name()}}]}})
    results = []
    for point in response['points']:
        payload = point['payload']
        local = approved.get(payload.get('chunk_id'))
        if local is not None and payload.get('text') == local['exact_text']:
            results.append({**local, 'score':point['score']})
    results.sort(key=lambda r: -ranking_score(question, r))
    selected = results[:top_k]
    # An example never discards a nearby governing rule present in the same page.
    if retrieval_style(question) == 'example':
        pages = {r['source']['canonical_url'] for r in selected if r['source']['content_kind']=='example'}
        governing = next((r for r in results if r['source']['canonical_url'] in pages and
                          r['source']['content_kind'] in {'rule','condition'} and r not in selected), None)
        if governing:
            selected.append(governing)
    return selected
