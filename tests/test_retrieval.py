"""Public retrieval input and JSON-result contracts."""

import json
import math

import pytest

from rag_reliability_lab.models import Document
from rag_reliability_lab.retrieval import RetrievalError, retrieve


@pytest.fixture
def corpus():
    return (
        Document("doc-002", "Backup", "retention policy", ()),
        Document("doc-001", "Backup", "retention policy", ()),
        Document("doc-003", "Network", "route timeout", ()),
    )


def test_matched_results_are_ranked_serializable_and_body_free(corpus):
    results = retrieve(corpus, "backup")
    assert [result["document_id"] for result in results] == ["doc-001", "doc-002"]
    assert [result["rank"] for result in results] == [1, 2]
    assert results[0]["score"] == results[1]["score"]
    for result in results:
        assert set(result) == {"document_id", "title", "rank", "score"}
        assert result["title"] == "Backup"
        assert isinstance(result["score"], float)
        assert math.isfinite(result["score"]) and result["score"] > 0
    assert json.loads(json.dumps(results, allow_nan=False)) == results


def test_limits_and_short_results(corpus):
    assert [result["document_id"] for result in retrieve(corpus, "backup", k=1)] == [
        "doc-001"
    ]
    assert len(retrieve(corpus, "backup", k=20)) == 2
    assert [result["rank"] for result in retrieve(corpus, "network", k=20)] == [1]


@pytest.mark.parametrize("query", ["unmatched", "!!!", "中文"])
def test_unmatched_queries_have_no_zero_score_padding(corpus, query):
    assert retrieve(corpus, query) == []


@pytest.mark.parametrize("k", [True, False, 0, -1, 21, 1.0, "5", None])
def test_invalid_k_is_rejected(corpus, k):
    with pytest.raises(RetrievalError, match="k must be an integer between 1 and 20"):
        retrieve(corpus, "backup", k)


@pytest.mark.parametrize("query", ["", " \n\t", None, True, 42, ["backup"]])
def test_invalid_query_is_rejected(corpus, query):
    with pytest.raises(RetrievalError):
        retrieve(corpus, query)


def test_query_length_boundary_counts_supplied_characters(corpus):
    assert len(retrieve(corpus, "backup" + " " * 494)) == 2
    with pytest.raises(RetrievalError, match="at most 500 characters"):
        retrieve(corpus, "backup" + " " * 495)
    with pytest.raises(RetrievalError, match="at most 500 characters"):
        retrieve(corpus, "x" * 501)


def test_determinism_and_corpus_immutability(corpus):
    supplied = list(corpus)
    before = tuple(supplied)
    expected = retrieve(supplied, "BACKUP backup retention")
    assert retrieve(supplied, "retention backup") == expected
    assert retrieve(supplied, "BACKUP backup retention") == expected
    assert retrieve(iter(supplied), "retention backup") == expected
    assert tuple(supplied) == before
    assert supplied[0].body == "retention policy"
    # Returned dictionaries are independent of future calls and source objects.
    expected[0]["title"] = "Changed"
    assert retrieve(supplied, "backup")[0]["title"] == "Backup"
    assert supplied[0].title == "Backup"


@pytest.mark.parametrize(
    "corpus",
    [[], None, [False], [Document("doc-001", "---", "!!!", ())]],
)
def test_corpus_errors_use_public_retrieval_error(corpus):
    with pytest.raises(RetrievalError):
        retrieve(corpus, "backup")
