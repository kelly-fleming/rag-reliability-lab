"""Ordered batch retrieval evaluation using independent gold judgments."""

import math
import re
from collections.abc import Iterable
from typing import TypedDict

from rag_reliability_lab.metrics import (
    MetricsError,
    precision_at_k,
    recall_at_k,
    reciprocal_rank_at_k,
)
from rag_reliability_lab.models import Document, EvaluationQuery
from rag_reliability_lab.retrieval import RetrievalError, RetrievalResult, retrieve


class EvaluationError(ValueError):
    """A safe expected input or retrieval failure; no partial report is returned."""


class QueryMetrics(TypedDict):
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank_at_k: float


class AggregateMetrics(TypedDict):
    precision_at_k: float
    recall_at_k: float
    mrr_at_k: float


class QueryEvaluation(TypedDict):
    query_id: str
    question: str
    relevant_document_ids: list[str]
    results: list[RetrievalResult]
    metrics: QueryMetrics


class EvaluationResult(TypedDict):
    k: int
    doc_count: int
    query_count: int
    aggregate: AggregateMetrics
    per_query: list[QueryEvaluation]


def evaluate(
    corpus: Iterable[Document], queries: Iterable[EvaluationQuery], k: int = 5
) -> EvaluationResult:
    """Evaluate each query once in supplied order and macro-average all rows.

    No-hit queries contribute zero to each mean. Expected retrieval failures
    abort evaluation rather than silently producing artificial zero-hit rows.
    All query inputs are validated before retrieval starts. Returned collections
    are owned by this report; source documents and queries remain unchanged.
    """
    if isinstance(k, bool) or not isinstance(k, int) or not 1 <= k <= 20:
        raise EvaluationError("k must be an integer between 1 and 20.")
    try:
        documents = tuple(corpus)
        query_records = tuple(queries)
    except TypeError:
        raise EvaluationError(
            "Corpus and queries must be iterable collections."
        ) from None
    if not documents or any(not isinstance(doc, Document) for doc in documents):
        raise EvaluationError("Corpus must contain documents.")
    if any(not isinstance(doc.id, str) or not doc.id.strip() for doc in documents):
        raise EvaluationError("Corpus document IDs must be nonempty strings.")
    known_ids = {document.id for document in documents}
    if len(known_ids) != len(documents):
        raise EvaluationError("Corpus contains duplicate document IDs.")
    if not query_records:
        raise EvaluationError("Queries must not be empty.")
    seen = set()
    for query in query_records:
        if (
            not isinstance(query, EvaluationQuery)
            or not isinstance(query.id, str)
            or re.fullmatch(r"q-[0-9]{3}", query.id) is None
        ):
            raise EvaluationError("Each query must have an ID in format q-NNN.")
        if query.id in seen:
            raise EvaluationError("Queries contain duplicate query IDs.")
        seen.add(query.id)
        if (
            not isinstance(query.question, str)
            or not query.question.strip()
            or len(query.question) > 500
        ):
            raise EvaluationError(
                "Query questions must be nonblank strings of at most 500 characters."
            )
        try:
            # Reuse the metric boundary's nonempty/unique/string gold contract.
            recall_at_k((), query.relevant_document_ids, k)
        except MetricsError as error:
            raise EvaluationError(str(error)) from None
        if not set(query.relevant_document_ids) <= known_ids:
            raise EvaluationError("Query gold IDs reference an unknown document.")

    per_query: list[QueryEvaluation] = []
    for query in query_records:
        try:
            hits = retrieve(documents, query.question, k=k)
            ranked_ids = [hit["document_id"] for hit in hits]
            metrics = QueryMetrics(
                precision_at_k=precision_at_k(
                    ranked_ids, query.relevant_document_ids, k
                ),
                recall_at_k=recall_at_k(ranked_ids, query.relevant_document_ids, k),
                reciprocal_rank_at_k=reciprocal_rank_at_k(
                    ranked_ids, query.relevant_document_ids, k
                ),
            )
        except (RetrievalError, MetricsError) as error:
            raise EvaluationError(str(error)) from None
        per_query.append(
            QueryEvaluation(
                query_id=query.id,
                question=query.question,
                relevant_document_ids=list(query.relevant_document_ids),
                results=[RetrievalResult(**hit) for hit in hits],
                metrics=metrics,
            )
        )

    count = len(per_query)
    aggregate = AggregateMetrics(
        precision_at_k=math.fsum(row["metrics"]["precision_at_k"] for row in per_query)
        / count,
        recall_at_k=math.fsum(row["metrics"]["recall_at_k"] for row in per_query)
        / count,
        mrr_at_k=math.fsum(row["metrics"]["reciprocal_rank_at_k"] for row in per_query)
        / count,
    )
    return EvaluationResult(
        k=k,
        doc_count=len(documents),
        query_count=count,
        aggregate=aggregate,
        per_query=per_query,
    )
