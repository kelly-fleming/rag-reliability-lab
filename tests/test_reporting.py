"""Schema tests use toy evaluation data, never published benchmark claims."""

import copy
import json

import pytest

from rag_reliability_lab.bm25 import BM25Index
from rag_reliability_lab.evaluation import evaluate
from rag_reliability_lab.models import Document, EvaluationQuery
from rag_reliability_lab.reporting import ReportingError, serialize_report


@pytest.fixture
def evaluation_result():
    return {
        "k": 3,
        "doc_count": 2,
        "query_count": 1,
        "aggregate": {
            "precision_at_k": 1 / 3,
            "recall_at_k": 1.0,
            "mrr_at_k": 1 / 2,
        },
        "per_query": [
            {
                "query_id": "q-001",
                "question": "Fictional café?",
                "relevant_document_ids": ["doc-001"],
                "results": [
                    {
                        "document_id": "doc-002",
                        "title": "Other",
                        "rank": 1,
                        "score": 2.125,
                    },
                    {
                        "document_id": "doc-001",
                        "title": "Target",
                        "rank": 2,
                        "score": 1.23456789012345,
                    },
                ],
                "metrics": {
                    "precision_at_k": 1 / 3,
                    "recall_at_k": 1.0,
                    "reciprocal_rank_at_k": 1 / 2,
                },
            }
        ],
    }


def test_schema_keys_parameters_and_float_preservation(evaluation_result):
    serialized = serialize_report(evaluation_result)
    report = json.loads(serialized)
    assert set(report) == {
        "schema_version",
        "dataset_name",
        "algorithm",
        "algorithm_parameters",
        "k",
        "doc_count",
        "query_count",
        "aggregate",
        "per_query",
    }
    assert report["schema_version"] == "1"
    assert report["dataset_name"] == "synthetic-cloud-ops-v1"
    assert report["algorithm"] == "bm25"
    index = BM25Index([Document("doc-001", "Title", "Body", ())])
    assert report["algorithm_parameters"] == {"k1": index.k1, "b": index.b}
    for field in ("k", "doc_count", "query_count", "aggregate", "per_query"):
        assert report[field] == evaluation_result[field]
    assert isinstance(report["aggregate"]["precision_at_k"], float)
    assert "1.23456789012345" in serialized
    assert serialized.endswith("\n") and not serialized.endswith("\n\n")
    assert '\n  "' in serialized


def test_serialization_is_stable_and_does_not_mutate_input(evaluation_result):
    before = copy.deepcopy(evaluation_result)
    first = serialize_report(evaluation_result)
    assert serialize_report(evaluation_result).encode("utf-8") == first.encode("utf-8")
    reordered = dict(reversed(list(evaluation_result.items())))
    reordered["aggregate"] = dict(reversed(list(reordered["aggregate"].items())))
    assert serialize_report(reordered) == first
    assert evaluation_result == before


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("location", ["aggregate", "metrics", "score"])
def test_nonfinite_numbers_rejected(evaluation_result, value, location):
    if location == "aggregate":
        evaluation_result["aggregate"]["precision_at_k"] = value
    elif location == "metrics":
        evaluation_result["per_query"][0]["metrics"]["recall_at_k"] = value
    else:
        evaluation_result["per_query"][0]["results"][0]["score"] = value
    with pytest.raises(ReportingError):
        serialize_report(evaluation_result)


def test_no_incidental_metadata_or_extra_fields(evaluation_result, monkeypatch):
    monkeypatch.setenv("REPORT_PRIVATE_MARKER", "private-machine-marker")
    evaluation_result["host_path"] = "private-machine-marker"
    evaluation_result["per_query"][0]["timestamp"] = "private-machine-marker"
    evaluation_result["per_query"][0]["results"][0]["body"] = "private-machine-marker"
    serialized = serialize_report(evaluation_result)
    assert "private-machine-marker" not in serialized
    for forbidden in ("timestamp", "host_path", "environment", "body"):
        assert forbidden not in json.loads(serialized)
    del evaluation_result["aggregate"]
    with pytest.raises(ReportingError):
        serialize_report(evaluation_result)


def test_serializer_accepts_shared_evaluator_output():
    corpus = [Document("doc-001", "Synthetic", "backup", ())]
    queries = [EvaluationQuery("q-001", "backup", ("doc-001",))]
    result = evaluate(corpus, queries, k=1)
    report = json.loads(serialize_report(result))
    assert report["per_query"] == result["per_query"]
    assert report["aggregate"] == result["aggregate"]
