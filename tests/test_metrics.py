"""Independently authored exact fractions for retrieval metric definitions."""

import math

import pytest

from rag_reliability_lab.metrics import (
    MetricsError,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)

METRICS = (precision_at_k, recall_at_k, reciprocal_rank_at_k)


@pytest.mark.parametrize(
    ("retrieved", "gold", "k", "expected"),
    [
        (["a", "b"], ["a", "b"], 2, (1.0, 1.0, 1.0)),
        (["x", "a", "y"], ["a", "b"], 3, (1 / 3, 1 / 2, 1 / 2)),
        (["x", "y", "a", "b"], ["a", "b"], 3, (1 / 3, 1 / 2, 1 / 3)),
        (["a"], ["a", "b"], 5, (1 / 5, 1 / 2, 1.0)),
        (["a", "b", "c"], ["a", "b", "c"], 2, (1.0, 2 / 3, 1.0)),
        (["x", "y"], ["a", "b"], 2, (0.0, 0.0, 0.0)),
        (["x", "y", "a"], ["a"], 2, (0.0, 0.0, 0.0)),
        ([], ["a", "b", "c"], 4, (0.0, 0.0, 0.0)),
    ],
)
def test_independent_metric_fractions(retrieved, gold, k, expected):
    original_retrieved = retrieved.copy()
    original_gold = gold.copy()
    actual = tuple(metric(retrieved, gold, k) for metric in METRICS)
    assert actual == expected
    assert all(isinstance(value, float) and math.isfinite(value) for value in actual)
    assert retrieved == original_retrieved
    assert gold == original_gold


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize("k", [0, -1, True, False, 1.0, "2", None])
def test_invalid_k(metric, k):
    with pytest.raises(MetricsError):
        metric(["a"], ["a"], k)


@pytest.mark.parametrize("metric", METRICS)
@pytest.mark.parametrize(
    ("retrieved", "gold"),
    [
        (["a", "a"], ["a"]),
        (["x", "a", "a"], ["a"]),
        (["a"], ["a", "a"]),
        (["a"], []),
        ("a", ["a"]),
        (["a"], "a"),
        (None, ["a"]),
        (["a"], None),
        ([True], ["a"]),
        (["a"], [1]),
        ([" "], ["a"]),
        (["a"], [""]),
        ([["a"]], ["a"]),
    ],
)
def test_invalid_ids_rejected_even_beyond_cutoff(metric, retrieved, gold):
    with pytest.raises(MetricsError):
        metric(retrieved, gold, 1)


@pytest.mark.parametrize("metric", METRICS)
def test_iterables_and_repeated_calls(metric):
    expected = metric(["x", "a"], ["a", "b"], 2)
    assert metric(iter(["x", "a"]), iter(["a", "b"]), 2) == expected
    assert metric(["x", "a"], ["a", "b"], 2) == expected
