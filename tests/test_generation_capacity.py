from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock

from backend.llm import generation_capacity as capacity


def test_generation_capacity_queues_third_and_releases(monkeypatch):
    release, two_active = Event(), Event()
    lock = Lock()
    active = peak = 0

    def post(*args, **kwargs):
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
            if active == 2:
                two_active.set()
        assert release.wait(5)
        with lock:
            active -= 1
        return "ok"

    monkeypatch.setattr(capacity.requests, "post", post)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(capacity.generation_post, "url") for _ in range(3)]
        try:
            assert two_active.wait(5)
            assert sum(f.done() for f in futures) == 0
        finally:
            release.set()
        assert [f.result() for f in futures] == ["ok"] * 3
    assert peak == 2


def test_failed_generation_releases_capacity(monkeypatch):
    import pytest
    def fail(*args, **kwargs):
        raise RuntimeError("failed")
    monkeypatch.setattr(capacity.requests, "post", fail)
    for _ in range(3):
        with pytest.raises(RuntimeError):
            capacity.generation_post("url")
    monkeypatch.setattr(capacity.requests, "post", lambda *a, **kw: "ok")
    assert capacity.generation_post("url") == "ok"


def test_debug_stream_holds_capacity_until_closed(monkeypatch):
    class Response:
        def __enter__(self):
            return self
        def __exit__(self, *exc):
            return False
    monkeypatch.setattr(capacity.requests, "post", lambda *a, **kw: Response())
    with capacity.generation_post("url", stream=True):
        with capacity.generation_post("url", stream=True):
            assert not capacity._capacity.acquire(blocking=False)
    assert capacity._capacity.acquire(blocking=False)
    capacity._capacity.release()
