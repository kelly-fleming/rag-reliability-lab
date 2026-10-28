"""Run explicitly after `docker compose up --build -d --wait` (stdlib only)."""

import hashlib
import json
import subprocess
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def cli(*arguments):
    return subprocess.check_output(
        ["docker", "compose", "exec", "-T", "api", "rag-lab", *arguments], timeout=30
    )


def request(path, payload=None, *, raw=None):
    body = json.dumps(payload).encode() if payload is not None else raw
    req = Request(
        "http://127.0.0.1:8000" + path,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()


def fixture_hashes():
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in Path("data").glob("*.json")
    }


def main():
    before = fixture_hashes()
    assert request("/health") == (200, b'{"status":"ok"}')
    for path in ("/docs", "/openapi.json"):
        assert request(path)[0] == 200
    for k in (1, 5, 20):
        for query in ("backup retention", "NO-SUCH-ZEBRA", "!!!", "backup " * 70):
            status, body = request("/retrieve", {"query": query, "k": k})
            assert status == 200
            assert json.loads(body) == json.loads(
                cli("retrieve", "--query", query, "--k", str(k))
            )
        status, body = request("/evaluate", {"k": k})
        assert status == 200
        assert body == cli("evaluate", "--k", str(k))
        assert body == request("/evaluate", {"k": k})[1]
        report = json.loads(body)
        assert report["doc_count"] == 14 and report["query_count"] == 12
    for path in ("/retrieve", "/evaluate"):
        for payload in (
            {"query": "backup", "k": True},
            {"query": "backup", "k": 21},
            {"query": "x" * 501},
            {"query": "backup", "data_dir": "/private/path"},
            [],
        ):
            status, body = request(path, payload)
            assert status == 422
            assert json.loads(body) == {"detail": "Invalid request payload."}
        assert request(path, raw=b'{"query":')[0] == 422
    assert before == fixture_hashes()
    print(
        "Docker HTTP/CLI parity, repeatability, validation, docs, and fixtures: passed"
    )


if __name__ == "__main__":
    main()
