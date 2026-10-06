"""Process-local capacity for synchronous Ollama generation requests only.

Waiting callers queue; retrieval and deterministic calculation do not acquire
these slots. Hold the slot until the non-streaming HTTP request completes.
"""
from threading import BoundedSemaphore

import requests

MAX_CONCURRENT_GENERATIONS = 2
_capacity = BoundedSemaphore(MAX_CONCURRENT_GENERATIONS)


def generation_post(*args, **kwargs):
    from backend.llm.transport import selected_provider, fanar_ollama_payload
    if selected_provider() == "fanar":
        with _capacity:
            return fanar_ollama_payload(kwargs["json"])
    if kwargs.get("stream"):
        return _StreamingGeneration(args, kwargs)
    with _capacity:
        return requests.post(*args, **kwargs)


class _StreamingGeneration:
    """Debug streaming keeps capacity until its response context closes."""
    def __init__(self, args, kwargs):
        self.args, self.kwargs = args, kwargs

    def __enter__(self):
        _capacity.acquire()
        try:
            self.response = requests.post(*self.args, **self.kwargs)
            return self.response.__enter__()
        except BaseException:
            _capacity.release()
            raise

    def __exit__(self, *exc):
        try:
            return self.response.__exit__(*exc)
        finally:
            _capacity.release()
