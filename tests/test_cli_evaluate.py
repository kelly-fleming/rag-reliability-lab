"""Evaluation CLI output and explicit local artifact safeguards."""

import json
import os

import pytest

from rag_reliability_lab.cli import main
from rag_reliability_lab.dataset import load_dataset
from rag_reliability_lab.evaluation import evaluate
from rag_reliability_lab.reporting import serialize_report


@pytest.fixture
def data_dir(tmp_path):
    directory = tmp_path / "fixtures"
    directory.mkdir()
    documents = [
        {"id": "doc-001", "title": "Backup", "body": "retention", "tags": []},
        {"id": "doc-002", "title": "Network", "body": "routing", "tags": []},
    ]
    queries = [
        {
            "id": "q-001",
            "question": "backup",
            "relevant_document_ids": ["doc-001", "doc-002"],
        },
        {"id": "q-002", "question": "unmatched", "relevant_document_ids": ["doc-002"]},
    ]
    for name, records in (
        ("documents.json", documents),
        ("evaluation_queries.json", queries),
    ):
        (directory / name).write_text(json.dumps(records), encoding="utf-8")
    return directory


def arguments(data_dir, *extra):
    return ["evaluate", "--data-dir", str(data_dir), "--k", "2", *extra]


def snapshot(directory):
    return {
        str(path.relative_to(directory)): path.read_bytes()
        for path in directory.rglob("*")
        if path.is_file()
    }


def test_default_stdout_is_shared_report_without_file_writes(data_dir, capsys):
    before = snapshot(data_dir.parent)
    assert main(arguments(data_dir)) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    report = json.loads(captured.out)
    assert report["schema_version"] == "1"
    assert report["query_count"] == 2
    assert report["aggregate"] == {
        "precision_at_k": 1 / 4,
        "recall_at_k": 1 / 4,
        "mrr_at_k": 1 / 2,
    }
    assert captured.out == serialize_report(evaluate(*load_dataset(data_dir), k=2))
    assert main(arguments(data_dir)) == 0
    assert capsys.readouterr().out == captured.out
    assert snapshot(data_dir.parent) == before


def test_explicit_output_creates_parents_and_matches_stdout(data_dir, capsys):
    assert main(arguments(data_dir)) == 0
    expected = capsys.readouterr().out
    output = data_dir.parent / "reports" / "nested" / "report.json"
    assert main(arguments(data_dir, "--output", str(output))) == 0
    captured = capsys.readouterr()
    assert captured.out == captured.err == ""
    assert output.read_bytes() == expected.encode("utf-8")


def test_existing_output_requires_explicit_overwrite(data_dir, capsys):
    output = data_dir.parent / "report.json"
    output.write_text("original", encoding="utf-8")
    assert main(arguments(data_dir, "--output", str(output))) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "already exists" in captured.err
    assert output.read_text(encoding="utf-8") == "original"
    assert main(arguments(data_dir, "--output", str(output), "--overwrite")) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "1"


@pytest.mark.parametrize("name", ["documents.json", "evaluation_queries.json"])
def test_fixture_output_is_protected_even_with_overwrite(data_dir, capsys, name):
    output = data_dir / ".." / data_dir.name / name
    before = snapshot(data_dir)
    assert main(arguments(data_dir, "--output", str(output), "--overwrite")) == 1
    captured = capsys.readouterr()
    assert "must not replace dataset fixtures" in captured.err
    assert captured.out == ""
    assert snapshot(data_dir) == before


def test_hard_link_to_fixture_is_protected(data_dir, capsys):
    output = data_dir.parent / "alias.json"
    try:
        os.link(data_dir / "documents.json", output)
    except OSError:
        pytest.skip("Filesystem does not support creating hard links")
    before = output.read_bytes()
    assert main(arguments(data_dir, "--output", str(output), "--overwrite")) == 1
    assert "fixtures" in capsys.readouterr().err
    assert output.read_bytes() == before


@pytest.mark.parametrize("k", ["0", "21", "true", "1.5"])
def test_invalid_k_does_not_create_output(data_dir, capsys, k):
    output = data_dir.parent / "absent" / "report.json"
    assert main(arguments(data_dir, "--k", k, "--output", str(output))) in (1, 2)
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err
    assert not output.parent.exists()


def test_missing_data_is_safe_and_does_not_create_output(tmp_path, capsys):
    output = tmp_path / "absent" / "report.json"
    assert main(arguments(tmp_path / "private-missing", "--output", str(output))) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot read documents.json" in captured.err
    assert "private-missing" not in captured.err
    assert not output.parent.exists()


def test_overwrite_without_output_is_usage_error(data_dir, capsys):
    assert main(arguments(data_dir, "--overwrite")) == 2
    assert "requires --output" in capsys.readouterr().err


def test_output_io_failure_is_safe(data_dir, capsys):
    parent_file = data_dir.parent / "private-file"
    parent_file.write_text("unchanged", encoding="utf-8")
    assert main(arguments(data_dir, "--output", str(parent_file / "report.json"))) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Cannot write report output" in captured.err
    assert "private-file" not in captured.err
    assert parent_file.read_text(encoding="utf-8") == "unchanged"
