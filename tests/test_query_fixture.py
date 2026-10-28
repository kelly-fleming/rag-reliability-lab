"""Structural contracts for independently authored relevance labels."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_query_fixture_has_stable_ids_and_valid_relevance_sets():
    queries = json.loads(
        (ROOT / "data/evaluation_queries.json").read_text(encoding="utf-8")
    )
    documents = json.loads((ROOT / "data/documents.json").read_text(encoding="utf-8"))
    document_ids = {document["id"] for document in documents}

    assert isinstance(queries, list)
    assert 8 <= len(queries) <= 12
    query_ids = [query["id"] for query in queries]
    assert query_ids == [f"q-{number:03d}" for number in range(1, 13)]
    assert len(set(query_ids)) == len(query_ids)
    multi_relevant_count = 0
    for query in queries:
        assert set(query) == {"id", "question", "relevant_document_ids"}
        assert isinstance(query["question"], str)
        assert query["question"].strip()
        relevant_ids = query["relevant_document_ids"]
        assert isinstance(relevant_ids, list)
        assert relevant_ids
        assert all(isinstance(value, str) and value.strip() for value in relevant_ids)
        assert len(set(relevant_ids)) == len(relevant_ids)
        assert set(relevant_ids) <= document_ids
        if len(relevant_ids) > 1:
            multi_relevant_count += 1
    assert multi_relevant_count >= 2


def test_every_query_has_a_documented_relevance_justification():
    documentation = (ROOT / "docs/DATASET.md").read_text(encoding="utf-8")

    for number in range(1, 13):
        assert f"| q-{number:03d} |" in documentation
    assert "without executing retrieval" in documentation
