# Architecture

RAG Reliability Lab is a local, retrieval-only Python application. The layers
below are implemented in source; tests and runtime behavior remain unverified.

## Source and data boundaries

- `src/rag_reliability_lab/` contains the importable application package.
- `data/` holds checked-in fictional JSON fixtures, separate from application code.
- `tests/` holds independently authored regression cases.
- `docs/` describes behavior, dataset assumptions, and evaluation semantics.

## Processing layers

1. **JSON fixture loader:** Reads an explicit data directory, validates documents
   and relevance judgments, and returns immutable core objects. The default data
   directory is `./data` relative to the working directory, not an installed
   package resource. Loading is an explicit operation, never an import side effect.
2. **Tokenizer and BM25:** Pure tokenization feeds deterministic in-memory scoring
   over document titles and bodies. This layer has no filesystem or network I/O.
3. **Retrieval service:** Validates query and result-limit inputs and exposes one
   shared ranking contract for application callers, independently of HTTP or CLI.
4. **Evaluation metrics and batch evaluation:** Compares retrieved IDs with
   independently authored relevance judgments and aggregates per-query metrics.
   Reporting serializes these results without inventing benchmark claims.
5. **CLI and FastAPI adapters:** Parse interface inputs, call the same core
   services, and map expected errors to safe user-facing responses. The CLI owns
   explicitly requested report output; the API is intended for local read-only use.

`dataset.load_documents` serves retrieval without requiring gold fixtures;
`dataset.load_dataset` returns document/query tuples for evaluation. Frozen core
models own tuple collections. `tokenize.tokenize` is used by both BM25 document
indexing and query scoring. `retrieval.retrieve` validates inputs and returns
body-free typed result dictionaries. `evaluation.evaluate` calls that same
service for each query, then the pure `metrics` functions for gold comparisons.
`reporting.serialize_report` formats deterministic schema-1 JSON shared by CLI
evaluation and the HTTP evaluation route.

The CLI's `main` returns status codes and safe stderr errors. Only explicit
`evaluate --output` creates directories/files; overwrite permission does not
permit fixture replacement. `api.create_app` anchors server configuration once,
without reading fixtures. HTTP routes load data on request; health is liveness
only. Request bodies cannot choose filesystem paths. Launch the API on loopback
as described in [API.md](API.md).

Dependencies flow from adapters toward the core. The core must not import the
CLI or HTTP adapter. Fixture parsing owns input file access; ranking and metrics
operate on supplied data without modifying it. No layer requires cloud resources,
credentials, remote models, or answer generation.

## Import contract

Importing `rag_reliability_lab` exposes explicit version metadata only. It does
not load fixtures, perform retrieval, write files, contact a network, or start a
server. Future modules must keep operational work behind explicit calls rather
than expanding package initialization. The import smoke test disables Python's
bytecode cache writes to distinguish application side effects from interpreter
cache behavior.
