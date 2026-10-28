"""Real-interface parity against authored toy expectations, not benchmark scores."""

import json

import pytest
from fastapi.testclient import TestClient

from rag_reliability_lab.api import create_app
from rag_reliability_lab.cli import main
from rag_reliability_lab.dataset import load_dataset
from rag_reliability_lab.evaluation import evaluate
from rag_reliability_lab.reporting import serialize_report
from rag_reliability_lab.retrieval import retrieve


@pytest.fixture
def data_dir(tmp_path):
    # All three documents have four indexed tokens. The first two have the
    # same tokens with different spelling/case; ties must sort by ID, not input.
    documents = [
        {"id": "doc-002", "title": "ALPHA GATE", "body": "backup 7", "tags": []},
        {"id": "doc-001", "title": "Alpha-Gate", "body": "Backup_7", "tags": []},
        {
            "id": "doc-003",
            "title": "Network Route",
            "body": "private timeout",
            "tags": [],
        },
    ]
    queries = [
        {
            "id": "q-003",
            "question": "ALPHA-GATE backup_7 backup_7",
            "relevant_document_ids": ["doc-002", "doc-003"],
        },
        {
            "id": "q-001",
            "question": "NO-SUCH-ZEBRA",
            "relevant_document_ids": ["doc-001"],
        },
        {
            "id": "q-002",
            "question": "PRIVATE-timeout",
            "relevant_document_ids": ["doc-003"],
        },
    ]
    for filename, records in (
        ("documents.json", documents),
        ("evaluation_queries.json", queries),
    ):
        (tmp_path / filename).write_text(json.dumps(records), encoding="utf-8")
    return tmp_path


def snapshot(directory):
    return {
        path.name: path.read_bytes() for path in directory.iterdir() if path.is_file()
    }


def cli_json(data_dir, capsys, command, k, *extra):
    assert main([command, "--data-dir", str(data_dir), "--k", str(k), *extra]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    return captured.out


@pytest.mark.parametrize("k", [2, 3])
def test_real_interfaces_match_authored_rankings_and_fractions(data_dir, capsys, k):
    before = snapshot(data_dir)
    documents, queries = load_dataset(data_dir)
    # These targets are authored from the fixture, never computed by a ranker.
    expected_ids = [["doc-001", "doc-002"], [], ["doc-003"]]
    expected_per_query = [
        {
            "precision_at_k": 1 / k,
            "recall_at_k": 1 / 2,
            "reciprocal_rank_at_k": 1 / 2,
        },
        {
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "reciprocal_rank_at_k": 0.0,
        },
        {
            "precision_at_k": 1 / k,
            "recall_at_k": 1.0,
            "reciprocal_rank_at_k": 1.0,
        },
    ]
    # Two queries each hit one gold document; all three remain in the mean.
    expected_aggregate = {
        "precision_at_k": (1 / k + 0 + 1 / k) / 3,
        "recall_at_k": 1 / 2,
        "mrr_at_k": 1 / 2,
    }
    with TestClient(create_app(data_dir)) as client:
        for query, ranked_ids in zip(queries, expected_ids, strict=True):
            direct = retrieve(documents, query.question, k=k)
            cli_text = cli_json(
                data_dir, capsys, "retrieve", k, "--query", query.question
            )
            http = client.post("/retrieve", json={"query": query.question, "k": k})
            assert http.status_code == 200
            for results in (direct, json.loads(cli_text), http.json()):
                assert [hit["document_id"] for hit in results] == ranked_ids
                assert [hit["rank"] for hit in results] == list(
                    range(1, len(ranked_ids) + 1)
                )
            assert json.loads(cli_text) == direct == http.json()
            assert cli_json(
                data_dir, capsys, "retrieve", k, "--query", query.question
            ).encode("utf-8") == cli_text.encode("utf-8")

        direct_report = evaluate(documents, queries, k=k)
        direct_text = serialize_report(direct_report)
        cli_text = cli_json(data_dir, capsys, "evaluate", k)
        http = client.post("/evaluate", json={"k": k})
        assert http.status_code == 200
        assert cli_text.encode("utf-8") == direct_text.encode("utf-8") == http.content
        for report in (direct_report, json.loads(cli_text), http.json()):
            assert [row["query_id"] for row in report["per_query"]] == [
                "q-003",
                "q-001",
                "q-002",
            ]
            assert [row["metrics"] for row in report["per_query"]] == expected_per_query
            assert report["aggregate"] == expected_aggregate
            assert [
                [hit["document_id"] for hit in row["results"]]
                for row in report["per_query"]
            ] == expected_ids
            assert [row["relevant_document_ids"] for row in report["per_query"]] == [
                ["doc-002", "doc-003"],
                ["doc-001"],
                ["doc-003"],
            ]
        assert serialize_report(evaluate(documents, queries, k=k)) == direct_text
        assert cli_json(data_dir, capsys, "evaluate", k) == cli_text
        assert client.post("/evaluate", json={"k": k}).content == http.content
    assert snapshot(data_dir) == before
    assert set(path.name for path in data_dir.iterdir()) == set(before)


def test_changing_only_gold_changes_metrics_not_predictions(data_dir, capsys):
    original_documents = (data_dir / "documents.json").read_bytes()
    path = data_dir / "evaluation_queries.json"
    with TestClient(create_app(data_dir)) as client:
        before = client.post("/evaluate", json={"k": 2})
        assert before.status_code == 200
        # Explicitly change only the first gold set, leaving query text intact.
        records = json.loads(path.read_text(encoding="utf-8"))
        records[0]["relevant_document_ids"] = ["doc-001"]
        path.write_text(json.dumps(records), encoding="utf-8")
        changed_snapshot = snapshot(data_dir)
        documents, queries = load_dataset(data_dir)
        direct = evaluate(documents, queries, k=2)
        cli_text = cli_json(data_dir, capsys, "evaluate", 2)
        after = client.post("/evaluate", json={"k": 2})
        assert after.status_code == 200
        assert after.text == cli_text == serialize_report(direct)
    for old, new in zip(before.json()["per_query"], direct["per_query"], strict=True):
        assert old["results"] == new["results"]
        assert old["question"] == new["question"]
    assert direct["per_query"][0]["relevant_document_ids"] == ["doc-001"]
    assert direct["per_query"][0]["metrics"] == {
        "precision_at_k": 1 / 2,
        "recall_at_k": 1.0,
        "reciprocal_rank_at_k": 1.0,
    }
    assert direct["aggregate"] == {
        "precision_at_k": 1 / 3,
        "recall_at_k": 2 / 3,
        "mrr_at_k": 2 / 3,
    }
    assert (data_dir / "documents.json").read_bytes() == original_documents
    assert snapshot(data_dir) == changed_snapshot
