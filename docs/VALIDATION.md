# Validation

Release verification completed on 2026-10-28. All 326 tests, lint, formatting,
package builds, and Docker API/CLI smoke checks passed. Docker startup, restart,
health recovery, and retrieval without runtime network access were verified.
Version 0.1.0 is ready for local retrieval and evaluation use. The
resolver-generated `uv.lock` is included. These checks establish implementation
behavior, not real-world benchmark quality or production security assurance.

To reproduce the checks, run from the repository root with uv installed:

```bash
uv python install 3.12
uv sync --locked
uv run --locked python -c "import rag_reliability_lab"
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

For dependency updates, run `uv lock`, review its resolver output, and keep
`uv.lock` alongside the corresponding implementation. Keep virtual environments,
reports, secrets, and caches out of source control. Fix check failures and rerun
the checks without weakening assertions or suppressing failures.

CLI and API verification covered retrieval/evaluation parity, repeatability,
no-match queries, strict input limits, safe errors, and unchanged fixtures.
Reproduce retrieval and evaluation with:

```bash
uv run --locked rag-lab retrieve --query "backup retention" --k 5
uv run --locked rag-lab evaluate --k 5
uv run --locked uvicorn rag_reliability_lab.api:app --host 127.0.0.1 --port 8000
```

Keep the server bound to loopback. In another terminal use the payloads in
[API.md](API.md) to inspect `/health`, `/retrieve`, `/evaluate`, and `/docs`.

For the container checks, use the [Docker quickstart](../README.md#docker-quickstart)
and run `python tests/docker_smoke.py` against the local container. The smoke
checks compare CLI/API output at k=1,5,20 and verify strict request handling.

Corpus and relevance rationales have been reviewed for coherence. For benchmark
comparisons, review label suitability and report observed evaluation output
with its version and configuration. The synthetic dataset does not represent
real operational performance.
