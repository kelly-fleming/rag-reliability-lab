"""Temporary-fixture coverage for the strict read-only dataset boundary."""

import copy
import json
from dataclasses import FrozenInstanceError

import pytest

from rag_reliability_lab.dataset import DatasetError, load_dataset, load_documents
from rag_reliability_lab.models import Document, EvaluationQuery


@pytest.fixture
def records():
    return (
        [
            {"id": " doc-002 ", "title": " Two ", "body": "line 1\nline 2", "tags": []},
            {"id": "doc-001", "title": "One", "body": " Body ", "tags": [" tag "]},
        ],
        [
            {
                "id": " q-002 ",
                "question": " Question? ",
                "relevant_document_ids": ["doc-001", "doc-002"],
            },
            {"id": "q-001", "question": "Other?", "relevant_document_ids": ["doc-002"]},
        ],
    )


def write_fixtures(directory, documents, queries):
    (directory / "documents.json").write_text(json.dumps(documents), encoding="utf-8")
    (directory / "evaluation_queries.json").write_text(
        json.dumps(queries), encoding="utf-8"
    )


def test_valid_dataset_is_ordered_immutable_and_read_only(tmp_path, records):
    documents, queries = records
    original = copy.deepcopy(records)
    write_fixtures(tmp_path, documents, queries)
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}

    loaded_documents, loaded_queries = load_dataset(tmp_path)

    assert loaded_documents == (
        Document("doc-002", "Two", "line 1\nline 2", ()),
        Document("doc-001", "One", "Body", ("tag",)),
    )
    assert loaded_queries == (
        EvaluationQuery("q-002", "Question?", ("doc-001", "doc-002")),
        EvaluationQuery("q-001", "Other?", ("doc-002",)),
    )
    with pytest.raises(FrozenInstanceError):
        loaded_documents[0].title = "Changed"
    with pytest.raises(FrozenInstanceError):
        loaded_queries[0].question = "Changed"
    assert isinstance(loaded_documents, tuple)
    assert isinstance(loaded_queries, tuple)
    assert isinstance(loaded_documents[1].tags, tuple)
    assert isinstance(loaded_queries[0].relevant_document_ids, tuple)
    assert records == original
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before


def test_models_own_collection_values():
    tags = ["tag"]
    relevant = ["doc-001"]
    document = Document("doc-001", "Title", "Body", tags)
    query = EvaluationQuery("q-001", "Question", relevant)
    tags.append("new")
    relevant.clear()
    assert document.tags == ("tag",)
    assert query.relevant_document_ids == ("doc-001",)


@pytest.mark.parametrize("fixture_index", [0, 1])
@pytest.mark.parametrize("root", [{}, True, None, "private payload", 7, []])
def test_invalid_roots(tmp_path, records, fixture_index, root):
    fixtures = list(records)
    fixtures[fixture_index] = root
    write_fixtures(tmp_path, *fixtures)
    with pytest.raises(DatasetError):
        load_dataset(tmp_path)


@pytest.mark.parametrize(
    ("fixture_index", "field", "value"),
    [
        (0, "id", True),
        (0, "id", "doc-1"),
        (0, "id", "doc-００１"),
        (0, "title", " \t"),
        (0, "body", False),
        (0, "body", "\n"),
        (0, "tags", "tag"),
        (0, "tags", [False]),
        (0, "tags", [" "]),
        (0, "tags", [["nested"]]),
        (1, "id", "doc-001"),
        (1, "id", 1),
        (1, "question", " "),
        (1, "question", {"nested": "value"}),
        (1, "relevant_document_ids", []),
        (1, "relevant_document_ids", "doc-001"),
        (1, "relevant_document_ids", [True]),
        (1, "relevant_document_ids", [" "]),
        (1, "relevant_document_ids", ["doc-999"]),
        (1, "relevant_document_ids", ["doc-1"]),
        (1, "relevant_document_ids", ["doc-001", " doc-001 "]),
    ],
)
def test_invalid_fields(tmp_path, records, fixture_index, field, value):
    records[fixture_index][0][field] = value
    write_fixtures(tmp_path, *records)
    with pytest.raises(DatasetError):
        load_dataset(tmp_path)


@pytest.mark.parametrize("fixture_index", [0, 1])
@pytest.mark.parametrize("change", ["missing", "extra", "duplicate", "nonobject"])
def test_record_schema_and_duplicate_ids(tmp_path, records, fixture_index, change):
    fixture = records[fixture_index]
    if change == "missing":
        del fixture[0]["id"]
    elif change == "extra":
        fixture[0]["private-unexpected-field"] = "private payload"
    elif change == "duplicate":
        fixture.append(copy.deepcopy(fixture[0]))
    else:
        fixture[0] = False
    write_fixtures(tmp_path, *records)
    with pytest.raises(DatasetError) as error:
        load_dataset(tmp_path)
    assert "private" not in str(error.value)


@pytest.mark.parametrize("filename", ["documents.json", "evaluation_queries.json"])
@pytest.mark.parametrize(
    "payload",
    [b'{"private payload":', b'[{"id":1,"id":2}]', b"[NaN]", b"\xff"],
)
def test_malformed_json_and_encoding_are_safe(tmp_path, records, filename, payload):
    write_fixtures(tmp_path, *records)
    (tmp_path / filename).write_bytes(payload)
    with pytest.raises(DatasetError) as error:
        load_dataset(tmp_path)
    assert "private payload" not in str(error.value)
    assert str(tmp_path) not in str(error.value)


def test_missing_files_and_directories_are_safe(tmp_path, records):
    missing = tmp_path / "private-directory"
    with pytest.raises(DatasetError, match=r"^Cannot read documents.json as UTF-8\.$"):
        load_documents(missing)
    assert not missing.exists()
    write_fixtures(tmp_path, *records)
    (tmp_path / "evaluation_queries.json").unlink()
    with pytest.raises(DatasetError) as error:
        load_dataset(tmp_path)
    assert str(tmp_path) not in str(error.value)
    # Retrieval-only loading must not require evaluation queries.
    assert len(load_documents(tmp_path)) == 2


def test_default_directory_is_relative_to_working_directory(
    tmp_path, records, monkeypatch
):
    directory = tmp_path / "data"
    directory.mkdir()
    write_fixtures(directory, *records)
    monkeypatch.chdir(tmp_path)
    assert load_dataset() == load_dataset(directory)


def test_unreadable_file_is_a_dataset_error(tmp_path, monkeypatch):
    def deny_read(*args, **kwargs):
        raise PermissionError("private filesystem details")

    monkeypatch.setattr("pathlib.Path.read_text", deny_read)
    with pytest.raises(DatasetError) as error:
        load_documents(tmp_path)
    assert "private" not in str(error.value)
