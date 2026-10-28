"""Local API contracts using temporary fictional fixtures only."""

import json

import pytest
from fastapi.testclient import TestClient

from rag_reliability_lab import api
from rag_reliability_lab.api import create_app
from rag_reliability_lab.dataset import load_dataset
from rag_reliability_lab.evaluation import evaluate
from rag_reliability_lab.reporting import serialize_report
from rag_reliability_lab.retrieval import retrieve


@pytest.fixture
def data_dir(tmp_path):
    documents = [
        {"id": "doc-001", "title": "Backup", "body": "retention", "tags": []},
        {"id": "doc-002", "title": "Network", "body": "route", "tags": []},
    ]
    queries = [
        {"id": "q-001", "question": "backup", "relevant_document_ids": ["doc-001"]},
        {"id": "q-002", "question": "unmatched", "relevant_document_ids": ["doc-002"]},
    ]
    for name, records in (
        ("documents.json", documents),
        ("evaluation_queries.json", queries),
    ):
        (tmp_path / name).write_text(json.dumps(records), encoding="utf-8")
    return tmp_path


def test_health_and_construction_do_not_read_fixtures(tmp_path, monkeypatch):
    def unexpected_read(*args, **kwargs):
        raise AssertionError("Construction and health must not load fixtures")

    monkeypatch.setattr(api, "load_documents", unexpected_read)
    monkeypatch.setattr(api, "load_dataset", unexpected_read)
    with TestClient(create_app(tmp_path / "missing")) as client:
        assert client.get("/health").json() == {"status": "ok"}


def test_valid_routes_use_shared_services_without_writes(data_dir):
    before = {path.name: path.read_bytes() for path in data_dir.iterdir()}
    documents, queries = load_dataset(data_dir)
    with TestClient(create_app(data_dir)) as client:
        response = client.post("/retrieve", json={"query": "backup", "k": 1})
        assert response.status_code == 200
        assert response.json() == retrieve(documents, "backup", k=1)
        assert client.post("/retrieve", json={"query": "unmatched"}).json() == []
        report = client.post("/evaluate", json={"k": 2})
        assert report.status_code == 200
        assert report.text == serialize_report(evaluate(documents, queries, k=2))
        assert report.json()["aggregate"] == {
            "precision_at_k": 1 / 4,
            "recall_at_k": 1 / 2,
            "mrr_at_k": 1 / 2,
        }
        assert client.post("/evaluate", json={}).json()["k"] == 5
        assert client.post("/retrieve", json={"query": "backup"}).status_code == 200
    assert {path.name: path.read_bytes() for path in data_dir.iterdir()} == before


@pytest.mark.parametrize("route", ["/retrieve", "/evaluate"])
@pytest.mark.parametrize("k", [True, False, 0, 21, 1.0, "5", None, {}])
def test_strict_limit_validation(data_dir, route, k):
    payload = {"k": k}
    if route == "/retrieve":
        payload["query"] = "backup"
    with TestClient(create_app(data_dir)) as client:
        assert client.post(route, json=payload).status_code == 422


@pytest.mark.parametrize(
    "query", ["", " \t", "x" * 501, True, 1, None, {"nested": "value"}]
)
def test_invalid_query(data_dir, query):
    with TestClient(create_app(data_dir)) as client:
        assert client.post("/retrieve", json={"query": query}).status_code == 422


def test_query_length_boundary(data_dir):
    with TestClient(create_app(data_dir)) as client:
        assert (
            client.post("/retrieve", json={"query": "backup" + " " * 494}).status_code
            == 200
        )
        assert (
            client.post("/retrieve", json={"query": "backup" + " " * 495}).status_code
            == 422
        )


@pytest.mark.parametrize("route", ["/retrieve", "/evaluate"])
def test_unknown_fields_and_malformed_bodies_are_safe(data_dir, route):
    with TestClient(create_app(data_dir)) as client:
        payload = {"data_dir": "/private/fixture-path"}
        if route == "/retrieve":
            payload["query"] = "backup"
        response = client.post(route, json=payload)
        assert response.status_code == 422
        assert "private" not in response.text
        for payload in ([], "text", 42):
            assert client.post(route, json=payload).status_code == 422
        assert (
            client.post(
                route,
                content=b'{"private":',
                headers={"Content-Type": "application/json"},
            ).status_code
            == 422
        )
        assert client.post(route).status_code == 422


def test_dataset_failure_is_safe_and_no_write_routes_exist(tmp_path):
    with TestClient(create_app(tmp_path / "private-missing")) as client:
        for route, payload in (("/retrieve", {"query": "backup"}), ("/evaluate", {})):
            response = client.post(route, json=payload)
            assert response.status_code == 503
            assert "private-missing" not in response.text
            assert "Traceback" not in response.text
        for method in ("put", "patch", "delete"):
            assert getattr(client, method)("/retrieve").status_code == 405
        assert client.post("/documents", json={}).status_code == 404


def test_openapi_inputs_and_no_permissive_cors(data_dir):
    with TestClient(create_app(data_dir)) as client:
        schema = client.get("/openapi.json").json()
        request_schema = schema["components"]["schemas"]["RetrieveRequest"]
        assert request_schema["additionalProperties"] is False
        assert request_schema["properties"]["query"]["maxLength"] == 500
        assert request_schema["properties"]["k"]["minimum"] == 1
        assert request_schema["properties"]["k"]["maximum"] == 20
        response = client.get("/health", headers={"Origin": "https://example.invalid"})
        assert "access-control-allow-origin" not in response.headers
