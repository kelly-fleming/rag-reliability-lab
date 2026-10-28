"""Predetermined rankings isolate gold-label aggregation from BM25."""

import pytest

from rag_reliability_lab import evaluation
from rag_reliability_lab.evaluation import EvaluationError, evaluate
from rag_reliability_lab.models import Document, EvaluationQuery
from rag_reliability_lab.retrieval import RetrievalError


@pytest.fixture
def corpus():
    return tuple(
        Document(f"doc-{n:03d}", "Shared title", "Shared body", ()) for n in range(1, 4)
    )


def test_macro_means_include_zero_hit_and_multi_gold(corpus, monkeypatch):
    queries = (
        EvaluationQuery("q-003", "Multi gold", ("doc-001", "doc-003")),
        EvaluationQuery("q-001", "No hits", ("doc-002",)),
        EvaluationQuery("q-002", "First at two", ("doc-003",)),
    )
    predictions = {
        "Multi gold": ["doc-001", "doc-002"],
        "No hits": [],
        "First at two": ["doc-002", "doc-003"],
    }
    calls = []

    def fake_retrieve(documents, question, k=5):
        assert documents == corpus
        calls.append((question, k))
        return [
            {
                "document_id": identifier,
                "title": "Shared title",
                "rank": rank,
                "score": 1 / rank,
            }
            for rank, identifier in enumerate(predictions[question], start=1)
        ]

    monkeypatch.setattr(evaluation, "retrieve", fake_retrieve)
    report = evaluate(iter(corpus), iter(queries), k=2)
    assert calls == [(query.question, 2) for query in queries]
    assert report["k"] == 2
    assert report["doc_count"] == 3
    assert report["query_count"] == 3
    assert [row["query_id"] for row in report["per_query"]] == [
        "q-003",
        "q-001",
        "q-002",
    ]
    assert [row["question"] for row in report["per_query"]] == [
        q.question for q in queries
    ]
    assert [row["metrics"] for row in report["per_query"]] == [
        {"precision_at_k": 1 / 2, "recall_at_k": 1 / 2, "reciprocal_rank_at_k": 1.0},
        {"precision_at_k": 0.0, "recall_at_k": 0.0, "reciprocal_rank_at_k": 0.0},
        {"precision_at_k": 1 / 2, "recall_at_k": 1.0, "reciprocal_rank_at_k": 1 / 2},
    ]
    assert report["aggregate"] == {
        "precision_at_k": 1 / 3,
        "recall_at_k": 1 / 2,
        "mrr_at_k": 1 / 2,
    }
    first = report["per_query"][0]
    assert first["relevant_document_ids"] == ["doc-001", "doc-003"]
    assert [hit["document_id"] for hit in first["results"]] == ["doc-001", "doc-002"]
    assert [hit["score"] for hit in first["results"]] == [1.0, 0.5]
    first["relevant_document_ids"].clear()
    assert queries[0].relevant_document_ids == ("doc-001", "doc-003")


@pytest.mark.parametrize(
    "queries",
    [
        [],
        None,
        [False],
        [EvaluationQuery("bad", "Question", ("doc-001",))],
        [EvaluationQuery("q-001", " ", ("doc-001",))],
        [EvaluationQuery("q-001", "x" * 501, ("doc-001",))],
        [EvaluationQuery("q-001", "Question", ())],
        [EvaluationQuery("q-001", "Question", ("doc-999",))],
        [EvaluationQuery("q-001", "Question", (True,))],
        [EvaluationQuery("q-001", "Question", ("doc-001", "doc-001"))],
        [EvaluationQuery("q-001", "Question", ("doc-001",))] * 2,
    ],
)
def test_invalid_queries_rejected_before_retrieval(corpus, queries, monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Invalid query sets must be rejected before retrieval")

    monkeypatch.setattr(evaluation, "retrieve", unexpected_call)
    with pytest.raises(EvaluationError):
        evaluate(corpus, queries)


@pytest.mark.parametrize("k", [0, 21, True, 2.0, "2"])
def test_invalid_k(corpus, k):
    with pytest.raises(EvaluationError):
        evaluate(corpus, [EvaluationQuery("q-001", "Shared", ("doc-001",))], k=k)


def test_actual_shared_retrieval_is_used_and_repeats_are_stable(corpus):
    queries = [EvaluationQuery("q-001", "Shared", ("doc-003",))]
    report = evaluate(corpus, queries, k=2)
    assert evaluate(corpus, queries, k=2) == report
    assert [hit["document_id"] for hit in report["per_query"][0]["results"]] == [
        "doc-001",
        "doc-002",
    ]
    assert report["aggregate"] == {
        "precision_at_k": 0.0,
        "recall_at_k": 0.0,
        "mrr_at_k": 0.0,
    }


def test_retrieval_failure_is_not_silently_counted_as_no_hits(corpus, monkeypatch):
    def fail(*args, **kwargs):
        raise RetrievalError("Cannot score corpus.")

    monkeypatch.setattr(evaluation, "retrieve", fail)
    with pytest.raises(EvaluationError, match="Cannot score corpus"):
        evaluate(corpus, [EvaluationQuery("q-001", "Shared", ("doc-001",))])
