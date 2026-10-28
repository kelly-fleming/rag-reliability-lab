"""Pure gold-label retrieval metrics; no ranking or relevance inference.

All functions validate the complete supplied ID collections before applying the
top-k cutoff. Duplicate IDs are rejected rather than silently deduplicated.
An empty retrieved list is valid, but the independent gold set must be nonempty.
"""

from collections.abc import Iterable


class MetricsError(ValueError):
    """An expected failure validating metric inputs."""


def _ids(values: Iterable[str], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise MetricsError(f"{name} must be a collection of document IDs.")
    try:
        identifiers = tuple(values)
    except TypeError:
        raise MetricsError(f"{name} must be a collection of document IDs.") from None
    if any(not isinstance(value, str) or not value.strip() for value in identifiers):
        raise MetricsError(f"{name} must contain nonempty string document IDs.")
    if len(set(identifiers)) != len(identifiers):
        raise MetricsError(f"{name} must not contain duplicate document IDs.")
    return identifiers


def _inputs(
    retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int
) -> tuple[tuple[str, ...], frozenset[str]]:
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise MetricsError("k must be an integer greater than zero.")
    retrieved = _ids(retrieved_ids, "Retrieved IDs")
    relevant = _ids(relevant_ids, "Relevant IDs")
    if not relevant:
        raise MetricsError("Relevant IDs must not be empty.")
    return retrieved[:k], frozenset(relevant)


def precision_at_k(
    retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int
) -> float:
    """Return relevant hits in the first k results divided by k.

    Fewer than k results still use denominator k, including an empty ranking.
    """
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids, k)
    return sum(identifier in relevant for identifier in retrieved) / k


def recall_at_k(
    retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int
) -> float:
    """Return relevant hits in the first k results divided by all gold IDs."""
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids, k)
    return sum(identifier in relevant for identifier in retrieved) / len(relevant)


def reciprocal_rank_at_k(
    retrieved_ids: Iterable[str], relevant_ids: Iterable[str], k: int
) -> float:
    """Return 1 / first relevant rank within k, or 0.0 when none is present."""
    retrieved, relevant = _inputs(retrieved_ids, relevant_ids, k)
    for rank, identifier in enumerate(retrieved, start=1):
        if identifier in relevant:
            return 1 / rank
    return 0.0
