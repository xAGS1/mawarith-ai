from evaluation.rag_benchmark.run_retrieval_benchmark import recall, run, diagnostics


def test_recall_excludes_unjudged_questions_and_counts_failed_gold():
    records = [
        {"expected_source_ids": ["a", "b"], "results": [{"source_id": "a"}, {"source_id": "x"}, {"source_id": "b"}]},
        {"expected_source_ids": ["c"], "results": []},
        {"results": [{"source_id": "anything"}]},
    ]
    assert recall(records) == {"Recall@1": .25, "Recall@3": .5, "Recall@5": .5}


def test_retrieval_only_records_scores_provenance_and_review_flags():
    hit = {"text": "فإن لم يوجد صاحب فرض:", "score": .7,
           "source": {"chunk_id": "a", "source_name": "Approved", "section": "Inheritance"}}
    calls = []
    def retrieve(question, top_k):
        calls.append((question, top_k))
        return [hit, hit]
    result = run([{"id": "q", "question": "test", "expected_source_ids": ["a"]}], retrieve, 5)
    r = result["records"][0]
    assert calls == [("test", 5)]
    assert r["results"][0]["similarity_score"] == .7
    assert r["duplicate_ranks"] == [[1, 2]]
    assert r["suspicious_chunks"]
    assert not r["no_relevant_retrieval"]


def test_retrieval_failure_is_recorded_without_fake_metrics():
    def fail(*args, **kwargs):
        raise RuntimeError("Unavailable")
    result = run([{"id": "q", "question": "test"}], fail, 5)
    assert result["failed_questions"] == ["q"]
    assert result["metrics"]["Recall@1"] is None
    assert result["records"][0]["results"] == []
