import hashlib
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from backend.rag import dorar_ingestion as ingest
from backend.rag import dorar_retrieval as retrieval


def test_scope_discovery_excludes_other_books():
    document = '''<ul><li><a href="#">كتاب المواريث</a><ul>
    <li><a href="/feqhia/13638">تعريف</a></li></ul></li>
    <li><a href="#">كتاب آخر</a><ul><li><a href="/feqhia/1">غير متعلق</a></li></ul></li></ul>'''
    _, pages = ingest.discover_tree(document)
    assert list(pages) == ['https://dorar.net/feqhia/13638']
    assert ingest.article_url('https://dorar.net/feqhia/13638/title') == 'https://dorar.net/feqhia/13638'


@pytest.mark.parametrize('url', ['https://evil.example/feqhia/13638', '/hadith/1', '/feqhia',
    'http://dorar.net/feqhia/13638', 'https://dorar.net.evil.example/feqhia/13638'])
def test_url_validation(url):
    with pytest.raises(ValueError):
        ingest.article_url(url)


def meta():
    return {'page_title':'عنوان', 'hierarchy':['كتاب المواريث','باب','فصل'],
            'canonical_url':'https://dorar.net/feqhia/13638', 'sha256':'document-hash', 'fetched_at':'now'}


def test_article_extraction_keeps_qualifications_and_references():
    document = '''<div>بحث غير متعلق</div><div id="cntnt"><h1>عنوان</h1>
    <div class="w-100 mt-4"><span class="title-2">حكم</span><br>
    نص القاعدة <span class="tip">[1] المرجع (ص: 2)</span><br>
    إذا تحقق الشرط، إلا الاستثناء.<br>واختلف في ذلك.<br>
    <span class="title-2">مثال</span><br>نص المثال.</div>
    <h3 id="more-titles">انظر أيضا</h3><ul><li><a href="/feqhia/2">رابط</a></li></ul>
    <button>عرض الهوامش</button></div><footer>تذييل</footer>'''
    chunks, links = ingest.extract_chunks(document, meta())
    assert len(chunks) == 1
    text = chunks[0]['exact_text']
    assert all(s in text for s in ['القاعدة', 'الشرط', 'الاستثناء', 'واختلف', '[1] المرجع (ص: 2)'])
    assert all(s not in text for s in ['بحث غير متعلق', 'انظر أيضا', 'عرض الهوامش', 'تذييل'])
    assert 'نص المثال' in text
    assert chunks[0]['source']['excerpt_sha256'] == hashlib.sha256(text.encode()).hexdigest()
    assert links == [('https://dorar.net/feqhia/2','رابط')]


def test_unknown_markup_and_title_mismatch_rejected():
    with pytest.raises(ValueError):
        ingest.extract_chunks('<body>some other page</body>', meta())
    with pytest.raises(ValueError):
        ingest.extract_chunks('<div id="cntnt"><h1>غير متعلق</h1><div class="w-100">text</div></div>', meta())


def test_robots_disallow_stops_before_article_download(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'robots.http.json').write_text(json.dumps({'text':'User-agent: *\nDisallow: /feqhia/'}))
    session = Mock()
    session.headers = {}
    fetcher = ingest.CachedFetcher(tmp_path, session=session)
    with pytest.raises(PermissionError, match='disallows'):
        fetcher.check_policy()
    session.get.assert_not_called()


def test_cached_page_is_not_downloaded_again(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'robots.http.json').write_text(json.dumps({'text':'User-agent: *\nDisallow:'}))
    content = b'cached snapshot'
    (raw / '13638.html').write_bytes(content)
    (raw / '13638.http.json').write_text(json.dumps({'url':'https://dorar.net/feqhia/13638',
        'sha256':hashlib.sha256(content).hexdigest()}))
    session = Mock()
    session.headers = {}
    fetcher = ingest.CachedFetcher(tmp_path, session=session)
    fetcher.check_policy()
    assert fetcher.fetch(meta())[0] == content
    session.get.assert_not_called()


def test_uncached_access_requires_robots_check(tmp_path):
    fetcher = ingest.CachedFetcher(tmp_path)
    with pytest.raises(PermissionError):
        fetcher.fetch(meta())


def test_cached_canonical_url_cannot_change_article_scope(tmp_path):
    raw = tmp_path / 'raw'
    raw.mkdir()
    (raw / 'robots.http.json').write_text(json.dumps({'text':'User-agent: *\nDisallow:'}))
    content = b'<link rel="canonical" href="https://dorar.net/feqhia/1">'
    (raw / '13638.html').write_bytes(content)
    (raw / '13638.http.json').write_text(json.dumps({'url':'https://dorar.net/feqhia/13638',
        'sha256':hashlib.sha256(content).hexdigest()}))
    fetcher = ingest.CachedFetcher(tmp_path)
    fetcher.check_policy()
    with pytest.raises(ValueError, match='canonical URL'):
        fetcher.fetch(meta())


def test_oversized_coherent_blocks_are_quarantined_not_cut():
    document = '<div id="cntnt"><h1>عنوان</h1><div class="w-100">'+('نص ' * 3000)+'</div></div>'
    chunks, _ = ingest.extract_chunks(document, meta())
    assert len(chunks)==1 and chunks[0]['source']['retrieval_eligible'] is False


def test_behavior_is_not_misclassified_as_definition():
    assert ingest.content_kind('طريقة', 'فما خرج فهو نصيب الوارث.') != 'definition'
    assert ingest.content_kind('موضوع', 'التعريف: هو نصيب مقدر.') == 'definition'


def test_image_only_example_is_marked_without_ocr_or_invented_text():
    document = '<div id="cntnt"><h1>عنوان</h1><div class="w-100">مثال: <img src="table.png"></div></div>'
    chunks, _ = ingest.extract_chunks(document, meta())
    assert chunks[0]['source']['has_unextracted_visual'] is True
    assert chunks[0]['exact_text'] == 'مثال:'


def test_kind_ranking_is_semantic_score_plus_small_preferences():
    definition = {'score':.7,'source':{'source_type':'fiqh_reference','content_kind':'definition',
                                      'extraction_quality':'clean_html','topic':'term'}}
    other = {'score':.7,'source':{'source_type':'fiqh_reference','content_kind':'example','topic':'term'}}
    assert retrieval.ranking_score('ما معنى term؟', definition) > retrieval.ranking_score('ما معنى term؟', other)
    other['score']=.9
    assert retrieval.ranking_score('ما معنى term؟', other) > retrieval.ranking_score('ما معنى term؟', definition)


def test_no_processed_source_is_optional(monkeypatch, tmp_path):
    monkeypatch.setattr(retrieval, 'DATA_DIR', tmp_path)
    assert retrieval.dorar_candidates('question','query') == []


def test_indexing_is_source_scoped_and_upsert_precedes_pruning(monkeypatch):
    chunks, _ = ingest.extract_chunks('<div id="cntnt"><h1>عنوان</h1><div class="w-100">نص.</div></div>', meta())
    monkeypatch.setattr(retrieval,'load_dorar_chunks',lambda:chunks)
    monkeypatch.setattr(retrieval,'embed_texts',lambda _: [[1.] * 1024])
    store = Mock(collection='mawarith_fiqh')
    stored = []
    calls = []
    def call(method,path,body=None):
        calls.append((method,path,body))
        if method=='GET':
            return {'config':{'params':{'vectors':{'size':1024,'distance':'Cosine'}}}}
        if method=='PUT':
            stored.extend(body['points'])
        if path.endswith('/points'):
            return [{'id':p['id']} for p in stored]
        if path.endswith('/count'):
            return {'count':len(stored)}
        return {}
    store._request.side_effect=call
    monkeypatch.setattr(retrieval,'QdrantFiqhStore',lambda:store)
    assert retrieval.index_dorar()==1
    deletion=next(body for _,path,body in calls if '/delete' in path)
    assert deletion['filter']['must']==[{'key':'source_id','match':{'value':'dorar_fiqhia'}}]
    assert stored[0]['payload']['source_id']=='dorar_fiqhia'
    assert not any(method=='DELETE' for method,_,_ in calls)


def test_incomplete_index_does_not_delete(monkeypatch):
    chunks, _ = ingest.extract_chunks('<div id="cntnt"><h1>عنوان</h1><div class="w-100">نص.</div></div>', meta())
    monkeypatch.setattr(retrieval,'load_dorar_chunks',lambda:chunks)
    monkeypatch.setattr(retrieval,'embed_texts',lambda _: [[1.] * 1024])
    store=Mock(collection='mawarith_fiqh')
    store._request.side_effect=[{'config':{'params':{'vectors':{'size':1024,'distance':'Cosine'}}}}, {}, []]
    monkeypatch.setattr(retrieval,'QdrantFiqhStore',lambda:store)
    with pytest.raises(RuntimeError,match='incomplete'):
        retrieval.index_dorar()
    assert not any('/delete' in call.args[1] for call in store._request.call_args_list)
