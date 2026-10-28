"""Independent small-corpus arithmetic and deterministic ranking contracts."""

import math

import pytest

from rag_reliability_lab.bm25 import BM25Error, BM25Index
from rag_reliability_lab.models import Document


@pytest.fixture
def corpus():
    return (
        Document("doc-001", "Alpha", "alpha beta", ()),
        Document("doc-002", "Beta", "gamma", ()),
    )


def test_hand_calculated_scores(corpus):
    index = BM25Index(corpus)
    # Lengths 3 and 2; average 2.5. alpha df=1, beta df=2.
    # For alpha in doc-001: tf=2, normalization=.25+.75*1.2=1.15.
    alpha = index.score("alpha")
    assert [identifier for identifier, _ in alpha] == ["doc-001"]
    assert alpha[0][1] == pytest.approx(math.log(2) * 5 / 3.725)
    beta = index.score("beta")
    assert [identifier for identifier, _ in beta] == ["doc-002", "doc-001"]
    assert beta[0][1] == pytest.approx(math.log(1.2) * 2.5 / 2.275)
    assert beta[1][1] == pytest.approx(math.log(1.2) * 2.5 / 2.725)
    assert index.k1 == 1.5
    assert index.b == 0.75


def test_query_terms_are_unique_and_accumulation_is_deterministic(corpus):
    index = BM25Index(corpus)
    expected = index.score("alpha beta")
    assert index.score("BETA alpha alpha beta") == expected
    assert index.score("beta alpha") == expected
    assert index.score("alpha beta") == expected
    # Both terms contribute to doc-001, but only beta contributes to doc-002.
    assert expected[0][0] == "doc-001"
    assert expected[0][1] == pytest.approx(
        math.log(2) * 5 / 3.725 + math.log(1.2) * 2.5 / 2.725
    )


def test_ties_use_id_order_and_ignore_tags():
    corpus = (
        Document("doc-002", "same", "body", ("unique",)),
        Document("doc-001", "same", "body", ()),
    )
    index = BM25Index(corpus)
    hits = index.score("same")
    assert [identifier for identifier, _ in hits] == ["doc-001", "doc-002"]
    assert hits[0][1] == hits[1][1]
    assert index.score("unique") == []
    assert BM25Index(reversed(corpus)).score("same") == hits


@pytest.mark.parametrize("query", ["", " \t", "---", "unmatched", "中文"])
def test_empty_and_no_match_queries(corpus, query):
    assert BM25Index(corpus).score(query) == []


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("k1", 0),
        ("k1", -1),
        ("k1", True),
        ("k1", "1.5"),
        ("k1", float("nan")),
        ("k1", float("inf")),
        ("k1", 10**1000),
        ("b", -0.1),
        ("b", 1.1),
        ("b", False),
        ("b", None),
        ("b", float("nan")),
        ("b", float("-inf")),
    ],
)
def test_invalid_parameters(corpus, parameter, value):
    with pytest.raises(BM25Error):
        BM25Index(corpus, **{parameter: value})


@pytest.mark.parametrize("b", [0, 1])
def test_valid_boundary_parameters_and_large_k1(corpus, b):
    hits = BM25Index(corpus, k1=1e308, b=b).score("alpha beta")
    assert len(hits) == 2
    assert all(math.isfinite(score) and score > 0 for _, score in hits)


@pytest.mark.parametrize(
    "corpus",
    [
        (),
        None,
        (False,),
        (Document("doc-001", "", "", ()),),
        (Document("doc-001", "---", "中文", ()),),
        (Document("doc-001", "x", "y", ()), Document("doc-002", "", "", ())),
        (Document("doc-001", "x", "y", ()), Document("doc-001", "a", "b", ())),
    ],
)
def test_invalid_corpora(corpus):
    with pytest.raises(BM25Error):
        BM25Index(corpus)


def test_index_does_not_mutate_or_retain_mutable_corpus_list(corpus):
    supplied = list(corpus)
    index = BM25Index(supplied)
    assert supplied == list(corpus)
    supplied.clear()
    assert index.score("gamma")[0][0] == "doc-002"


def test_non_string_query_is_a_validation_error(corpus):
    with pytest.raises(BM25Error):
        BM25Index(corpus).score(True)
