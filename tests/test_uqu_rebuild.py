from unittest.mock import Mock
import pytest
from backend.rag import rebuild_uqu as rebuild


def test_only_uqu_can_be_indexed():
    with pytest.raises(ValueError, match='Only approved'):
        rebuild.index_uqu([{'text': 'text', 'source': {'source_id': 'other', 'verified_source': True}}])
    with pytest.raises(ValueError, match='Only approved'):
        rebuild.index_uqu([])


def test_safe_source_scoped_sync_never_touches_fiqh(monkeypatch):
    calls = []
    stored = []
    def request(method, url, json, timeout):
        calls.append((method, url, json))
        result = {}
        if url.endswith('/collections'):
            result = {'collections': [{'name': 'mawarith_fiqh'}]}
        elif method == 'PUT' and '/points?' in url:
            stored.extend(json['points'])
        elif url.endswith('/points'):
            result = [{'id': p['id']} for p in stored]
        elif url.endswith('/points/count'):
            result = {'count': len(stored)}
        return Mock(raise_for_status=Mock(), json=lambda: {'status': 'ok', 'result': result})
    monkeypatch.setattr(rebuild.requests, 'request', request)
    monkeypatch.setattr(rebuild, 'embed_texts', lambda _: [[1.] * 1024])
    source = {'source_id': 'uqu_mawarith_1', 'verified_source': True,
              'chunk_id': 'page-hash', 'char_start': 0, 'excerpt_sha256': 'excerpt-hash'}
    assert rebuild.index_uqu([{'text': 'exact source', 'source': source}]) == 1
    assert all('mawarith_fiqh' not in url for _, url, _ in calls)
    delete = next(body for _, url, body in calls if '/points/delete' in url)
    assert delete['filter']['must'][0]['match']['value'] == 'uqu_mawarith_1'
    assert delete['filter']['must_not'][0]['has_id'] == [stored[0]['id']]
    assert next(i for i, (_, url, _) in enumerate(calls) if url.endswith('/points')) < next(
        i for i, (_, url, _) in enumerate(calls) if '/points/delete' in url)


def test_incomplete_upsert_does_not_prune(monkeypatch):
    calls = []
    def request(method, url, json, timeout):
        calls.append(url)
        result = {'collections': []} if url.endswith('/collections') else []
        return Mock(raise_for_status=Mock(), json=lambda: {'status': 'ok', 'result': result})
    monkeypatch.setattr(rebuild.requests, 'request', request)
    monkeypatch.setattr(rebuild, 'embed_texts', lambda _: [[1.] * 1024])
    source = {'source_id': 'uqu_mawarith_1', 'verified_source': True,
              'chunk_id': 'page-hash', 'char_start': 0, 'excerpt_sha256': 'excerpt-hash'}
    with pytest.raises(RuntimeError, match='Incomplete UQU upsert'):
        rebuild.index_uqu([{'text': 'exact source', 'source': source}])
    assert not any('/delete' in url for url in calls)
