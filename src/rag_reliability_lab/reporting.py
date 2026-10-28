"""Deterministic JSON report schema version 1.

Top-level fields are schema_version="1", dataset_name="synthetic-cloud-ops-v1",
algorithm="bm25", algorithm_parameters={k1,b}, k, doc_count, query_count,
aggregate, and per_query. Aggregate contains precision_at_k, recall_at_k, and
mrr_at_k. Each per_query row contains query_id, question, relevant_document_ids,
results (document_id, title, rank, score), and metrics (precision_at_k,
recall_at_k, reciprocal_rank_at_k). Query/result/gold order follows evaluation.

Object keys are sorted, indentation is two spaces, Unicode is JSON-escaped,
and the string ends with one LF. Finite floats are emitted without rounding or
string conversion; NaN/Infinity are rejected. No timestamps, host paths, random
IDs, or environment metadata are added. Text from the supplied dataset remains
dataset content. Only named schema fields are serialized.
"""

import json

from rag_reliability_lab.bm25 import DEFAULT_B, DEFAULT_K1
from rag_reliability_lab.evaluation import EvaluationResult


class ReportingError(ValueError):
    """A safe failure serializing the supplied evaluation result."""


def serialize_report(evaluation: EvaluationResult) -> str:
    """Return schema-1 JSON for default-BM25 evaluate() output without I/O.

    This formats supplied evaluation data; it neither runs a benchmark nor
    recomputes scores. CLI and API callers can use the same string contract.
    """
    try:
        report = {
            "schema_version": "1",
            "dataset_name": "synthetic-cloud-ops-v1",
            "algorithm": "bm25",
            "algorithm_parameters": {"k1": DEFAULT_K1, "b": DEFAULT_B},
            "k": evaluation["k"],
            "doc_count": evaluation["doc_count"],
            "query_count": evaluation["query_count"],
            "aggregate": {
                name: evaluation["aggregate"][name]
                for name in ("precision_at_k", "recall_at_k", "mrr_at_k")
            },
            "per_query": [
                {
                    "query_id": row["query_id"],
                    "question": row["question"],
                    "relevant_document_ids": list(row["relevant_document_ids"]),
                    "results": [
                        {
                            name: hit[name]
                            for name in ("document_id", "title", "rank", "score")
                        }
                        for hit in row["results"]
                    ],
                    "metrics": {
                        name: row["metrics"][name]
                        for name in (
                            "precision_at_k",
                            "recall_at_k",
                            "reciprocal_rank_at_k",
                        )
                    },
                }
                for row in evaluation["per_query"]
            ],
        }
        return json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n"
    except (KeyError, TypeError, ValueError, OverflowError, RecursionError):
        raise ReportingError(
            "Cannot serialize evaluation report; required fields must be "
            "JSON-compatible and numbers finite."
        ) from None
