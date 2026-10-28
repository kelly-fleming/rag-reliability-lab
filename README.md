# RAG Reliability Lab

Release date: **0.1.0 - 2026-10-28**. GitHub publication is pending.
See [release notes](CHANGELOG.md).

v0.1.0 is a local, retrieval-only lab for experimenting with deterministic BM25
and independent relevance judgments. It ranks documents; it does not generate
answers or measure answer grounding. No LLM, embeddings, cloud resources, or
credentials are required to use the installed application.

Implemented source includes strict fixture loading, shared ASCII tokenization,
BM25 ranking, Precision@K/Recall@K/MRR@K evaluation, a CLI, a local FastAPI API,
and deterministic JSON reports. Local tests and Docker runtime checks have passed;
Maintainer approval is recorded; CI execution remains pending. No real-world
benchmark quality or throughput claim is made.

## Docker quickstart

From the repository root, with Docker Desktop running:

```bash
docker compose up --build -d --wait
docker compose exec api rag-lab retrieve --query "backup retention" --k 5
docker compose exec api rag-lab evaluate --k 5
docker compose --profile tools build test
docker compose run --rm test
docker compose run --rm test ruff check .
docker compose run --rm test ruff format --check .
python tests/docker_smoke.py
docker compose down
```

The API documentation is at `http://127.0.0.1:8000/docs`. Compose publishes only
to host loopback; Uvicorn listens on all interfaces inside its container so Docker
can forward requests. The runtime uses an unprivileged user and a read-only
filesystem, with the fictional fixtures included in the image. Rebuild after
source changes. Dependencies install during image build, with no install at
startup. CLI report export needs an explicitly writable destination, for example
an operator-mounted reports directory with permissions for UID 10001.

## Quickstart

Use Python 3.12 and uv. Run commands from this repository's root: fixtures default
to `./data`, not an installed package resource. Dependency installation requires
access to the package distributions; application retrieval/evaluation is local.

The resolver-generated `uv.lock` is included. Install its exact dependencies:

```bash
uv python install 3.12
uv sync --locked
uv run --locked rag-lab retrieve --query "backup retention" --k 5
uv run --locked rag-lab evaluate --k 5
```

Retrieval prints a JSON array of document IDs, titles, ranks, and finite scores.
No-match queries return `[]`. Evaluation prints the schema-1 report containing
each query's gold IDs, ranked results, metrics, macro averages, and BM25 defaults.
Both commands accept `--data-dir PATH` and k in 1..20. No files are written by
default. To explicitly export a local evaluation artifact:

```bash
uv run --locked rag-lab evaluate --k 5 --output reports/evaluation.json
```

Existing output is refused unless `--overwrite` is supplied; fixture destinations
are protected. Expected errors go to stderr with a nonzero exit status.

## Local API

```bash
uv run --locked uvicorn rag_reliability_lab.api:app --host 127.0.0.1 --port 8000
```

Keep the server bound to loopback. Open `http://127.0.0.1:8000/docs` to try
`POST /retrieve` with `{"query":"backup retention","k":5}` and `POST /evaluate`
with `{"k":5}`. `GET /health` reports process liveness without loading data.
The API uses the same core services as the CLI; see [API details](docs/API.md)
for strict payload rules, safe errors, and server-controlled dataset paths.

## Data and interpretation

The dataset contains fourteen wholly fictional cloud operations documents and
twelve independently authored questions, including multi-document gold sets and
intentional distractors. No live customer data, provider accounts, or secrets
are included. Gold judgments require operator review before publishing scores.

Read the [dataset and relevance rationales](docs/DATASET.md),
[metric definitions and limitations](docs/METRICS.md),
[architecture](docs/ARCHITECTURE.md), and [roadmap](ROADMAP.md).
Retrieval relevance does not establish factual correctness, safe operational
guidance, or the quality of a generated answer. BM25 scores are ranking signals,
not probabilities or confidence estimates.

## Validation

After installation, run:

```bash
uv run --locked python -c "import rag_reliability_lab"
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

Then run the CLI/API examples and review the gold labels. Follow the complete
[operator validation workflow](docs/VALIDATION.md). The authored
[CI workflow](.github/workflows/ci.yml) performs locked sync, lint, format, and
tests; its existence does not establish a successful run. Metric values must
not be claimed until tests and evaluation commands have actually executed.
