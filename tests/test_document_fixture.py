"""Structural expectations for the authored fictional corpus, not ranking."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_document_fixture_has_stable_unique_ids_and_nonempty_text():
    documents = json.loads((ROOT / "data/documents.json").read_text(encoding="utf-8"))

    assert isinstance(documents, list)
    assert 12 <= len(documents) <= 16
    ids = [document["id"] for document in documents]
    assert ids == [f"doc-{number:03d}" for number in range(1, 15)]
    assert len(set(ids)) == len(ids)
    for document in documents:
        assert set(document) == {"id", "title", "body", "tags"}
        for field in ("id", "title", "body"):
            assert isinstance(document[field], str)
            assert document[field].strip()
        assert isinstance(document["tags"], list)
        assert document["tags"]
        assert all(isinstance(tag, str) and tag.strip() for tag in document["tags"])


def test_dataset_documentation_declares_fictional_scope():
    documentation = (ROOT / "docs/DATASET.md").read_text(encoding="utf-8").lower()

    assert "synthetic-cloud-ops-v1" in documentation
    assert "all documents are wholly fictional" in documentation
    assert "not copied internal runbooks" in documentation
    assert "no real customers" in documentation
