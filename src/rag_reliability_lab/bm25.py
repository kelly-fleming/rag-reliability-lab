"""Deterministic, in-memory BM25 with no external search dependencies.

Title and body are joined with a separator and tokenized together. Titles have
no extra weighting in v0.1.0; tags are not indexed. Tokenless documents are
rejected even if their source strings contain nonempty punctuation or Unicode.
"""

import math
from collections import Counter
from collections.abc import Iterable

from rag_reliability_lab.models import Document
from rag_reliability_lab.tokenize import tokenize

DEFAULT_K1 = 1.5
DEFAULT_B = 0.75


class BM25Error(ValueError):
    """A safe validation failure constructing or scoring an index."""


def _parameter(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BM25Error(f"{name} must be a finite number.")
    try:
        number = float(value)
    except (OverflowError, ValueError):
        raise BM25Error(f"{name} must be a finite number.") from None
    if not math.isfinite(number):
        raise BM25Error(f"{name} must be a finite number.")
    return number


class BM25Index:
    """Build once from immutable documents, then score query strings read-only.

    score() returns (document ID, finite float score) pairs. Empty and unmatched
    queries produce no hits. Unique query tokens are accumulated in sorted order
    so hash randomization and query-term repetition cannot change scores.
    """

    def __init__(
        self,
        corpus: Iterable[Document],
        *,
        k1: float = DEFAULT_K1,
        b: float = DEFAULT_B,
    ) -> None:
        self._k1 = _parameter(k1, "k1")
        self._b = _parameter(b, "b")
        if self._k1 <= 0:
            raise BM25Error("k1 must be greater than zero.")
        if not 0 <= self._b <= 1:
            raise BM25Error("b must be between zero and one.")
        try:
            documents = tuple(corpus)
        except TypeError:
            raise BM25Error("Corpus must be an iterable of documents.") from None
        if not documents:
            raise BM25Error("Corpus must contain at least one document.")

        seen = set()
        frequencies = []
        lengths = []
        document_frequency = Counter()
        for document in documents:
            if (
                not isinstance(document, Document)
                or not isinstance(document.id, str)
                or not document.id.strip()
                or not isinstance(document.title, str)
                or not isinstance(document.body, str)
            ):
                raise BM25Error(
                    "Corpus must contain documents with string IDs and text."
                )
            if document.id in seen:
                raise BM25Error("Corpus contains duplicate document IDs.")
            seen.add(document.id)
            tokens = tokenize(document.title + "\n" + document.body)
            if not tokens:
                raise BM25Error(
                    "Each document must contain at least one indexed token."
                )
            counts = Counter(tokens)
            frequencies.append(counts)
            lengths.append(len(tokens))
            document_frequency.update(counts.keys())

        self._documents = documents
        self._frequencies = tuple(frequencies)
        self._lengths = tuple(lengths)
        self._average_length = sum(lengths) / len(documents)
        self._idf = {
            token: math.log1p((len(documents) - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }

    @property
    def k1(self) -> float:
        return self._k1

    @property
    def b(self) -> float:
        return self._b

    def score(self, query: str) -> list[tuple[str, float]]:
        """Rank positive matches, breaking exact score ties by document ID."""
        if not isinstance(query, str):
            raise BM25Error("Query must be a string.")
        terms = sorted(set(tokenize(query)))
        if not terms:
            return []
        results = []
        for document, counts, length in zip(
            self._documents, self._frequencies, self._lengths, strict=True
        ):
            normalization = 1 - self._b + self._b * (length / self._average_length)
            contributions = []
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                # Algebraically tf*(k1+1)/(tf+k1*normalization), scaled to
                # avoid overflowing tf*(k1+1) for large finite k1 values.
                saturation = frequency / (
                    frequency / (self._k1 + 1)
                    + (self._k1 / (self._k1 + 1)) * normalization
                )
                contributions.append(self._idf[term] * saturation)
            try:
                score = math.fsum(contributions)
            except OverflowError:
                raise BM25Error(
                    "BM25 score exceeds the finite numeric range."
                ) from None
            if not math.isfinite(score):
                raise BM25Error("BM25 score exceeds the finite numeric range.")
            if score > 0:
                results.append((document.id, score))
        return sorted(results, key=lambda result: (-result[1], result[0]))
