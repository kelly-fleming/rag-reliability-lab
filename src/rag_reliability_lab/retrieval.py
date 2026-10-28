"""Shared read-only retrieval service for evaluation, CLI, and HTTP callers."""

import math
from collections.abc import Iterable
from typing import TypedDict

from rag_reliability_lab.bm25 import BM25Error, BM25Index
from rag_reliability_lab.models import Document


class RetrievalError(ValueError):
    """A safe expected failure validating retrieval input or scoring a corpus."""


class RetrievalResult(TypedDict):
    """JSON-compatible result; full document bodies are deliberately omitted."""

    document_id: str
    title: str
    rank: int
    score: float


def retrieve(
    corpus: Iterable[Document], query: str, k: int = 5
) -> list[RetrievalResult]:
    """Return up to k positive BM25 hits with contiguous ranks starting at one.

    The 500-character limit applies to the supplied query before stripping outer
    whitespace. A nonblank query with no indexed tokens or no matches returns
    an empty list. k may exceed the matching result count; zero-score hits are
    never manufactured. The corpus is snapshotted and documents are not changed.
    No fixture loading, file writes, HTTP, or network operations occur here.
    """
    if not isinstance(query, str):
        raise RetrievalError("Query must be a string.")
    if not query.strip():
        raise RetrievalError("Query must not be empty or whitespace only.")
    if len(query) > 500:
        raise RetrievalError("Query must be at most 500 characters.")
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 20:
        raise RetrievalError("k must be an integer between 1 and 20.")

    try:
        documents = tuple(corpus)
    except TypeError:
        raise RetrievalError("Corpus must be an iterable of documents.") from None
    try:
        index = BM25Index(documents)
        hits = index.score(query.strip())
    except BM25Error as error:
        raise RetrievalError(str(error)) from None

    by_id = {document.id: document for document in documents}
    results: list[RetrievalResult] = []
    for rank, (document_id, score) in enumerate(hits[:k], start=1):
        if not math.isfinite(score) or score <= 0:
            raise RetrievalError("Retrieval requires finite positive scores.")
        results.append(
            RetrievalResult(
                document_id=document_id,
                title=by_id[document_id].title,
                rank=rank,
                score=float(score),
            )
        )
    return results
