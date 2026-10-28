"""Exercise the callable CLI using temporary corpus files and captured streams."""

import json
import sys

import pytest

from rag_reliability_lab.cli import main


@pytest.fixture
def data_dir(tmp_path):
    documents = [
        {"id": "doc-002", "title": "Backup", "body": "retention policy", "tags": []},
        {"id": "doc-001", "title": "Backup", "body": "retention policy", "tags": []},
        {"id": "doc-003", "title": "Network", "body": "route timeout", "tags": []},
    ]
    (tmp_path / "documents.json").write_text(json.dumps(documents), encoding="utf-8")
    # Retrieval must work without evaluation_queries.json.
    return tmp_path


def test_success_outputs_ranked_json_without_writes(data_dir, capsys):
    before = {path.name: path.read_bytes() for path in data_dir.iterdir()}
    status = main(["retrieve", "--query", "backup", "--data-dir", str(data_dir)])
    captured = capsys.readouterr()
    assert status == 0
    assert captured.err == ""
    results = json.loads(captured.out)
    assert [result["document_id"] for result in results] == ["doc-001", "doc-002"]
    assert [result["rank"] for result in results] == [1, 2]
    assert all(isinstance(result["score"], float) for result in results)
    assert all(
        set(result) == {"document_id", "title", "rank", "score"} for result in results
    )
    assert {path.name: path.read_bytes() for path in data_dir.iterdir()} == before


def test_explicit_limit(data_dir, capsys):
    assert (
        main(["retrieve", "--query", "backup", "--k", "1", "--data-dir", str(data_dir)])
        == 0
    )
    assert [row["document_id"] for row in json.loads(capsys.readouterr().out)] == [
        "doc-001"
    ]


@pytest.mark.parametrize("query", ["unmatched", "!!!"])
def test_no_matches_is_success_with_empty_json(data_dir, capsys, query):
    assert main(["retrieve", "--query", query, "--data-dir", str(data_dir)]) == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []
    assert captured.err == ""


@pytest.mark.parametrize("query", ["", " \t", "x" * 501])
def test_bad_query_is_controlled_error(data_dir, capsys, query):
    assert main(["retrieve", "--query", query, "--data-dir", str(data_dir)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Query must" in captured.err
    assert "Traceback" not in captured.err


@pytest.mark.parametrize("k", ["0", "-1", "21", "true", "1.5"])
def test_invalid_k_has_nonzero_status(data_dir, capsys, k):
    assert main(
        ["retrieve", "--query", "backup", "--k", k, "--data-dir", str(data_dir)]
    ) in (1, 2)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err
    assert "Traceback" not in captured.err


def test_missing_path_does_not_leak_host_path(tmp_path, capsys):
    missing = tmp_path / "private-location"
    assert main(["retrieve", "--query", "backup", "--data-dir", str(missing)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot read documents.json" in captured.err
    assert str(missing) not in captured.err
    assert not missing.exists()


def test_malformed_fixture_does_not_echo_contents(data_dir, capsys):
    (data_dir / "documents.json").write_text('{"private payload":', encoding="utf-8")
    assert main(["retrieve", "--query", "backup", "--data-dir", str(data_dir)]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Invalid JSON" in captured.err
    assert "private payload" not in captured.err


@pytest.mark.parametrize("argv", [[], ["retrieve"], ["unknown-command"]])
def test_usage_errors_return_status_two(argv, capsys):
    assert main(argv) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "usage:" in captured.err


def test_help_returns_zero(capsys):
    assert main(["retrieve", "--help"]) == 0
    captured = capsys.readouterr()
    assert "--query" in captured.out
    assert captured.err == ""


def test_none_argv_and_default_data_directory(data_dir, monkeypatch, capsys):
    directory = data_dir / "data"
    directory.mkdir()
    (data_dir / "documents.json").rename(directory / "documents.json")
    monkeypatch.chdir(data_dir)
    monkeypatch.setattr(sys, "argv", ["rag-lab", "retrieve", "--query", "network"])
    assert main() == 0
    assert json.loads(capsys.readouterr().out)[0]["document_id"] == "doc-003"
