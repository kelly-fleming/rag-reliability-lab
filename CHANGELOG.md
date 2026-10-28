# Changelog

## 0.1.0 - 2026-10-28

### Added

- Fourteen wholly fictional cloud operations documents and twelve independently
  authored relevance queries, including multi-document gold judgments.
- Strict UTF-8 fixture loading and immutable core values.
- Shared ASCII tokenization and deterministic BM25 with positive matches and
  document-ID tie ordering.
- Precision@K, Recall@K, and MRR@K with gold-only relevance and macro averages
  across all queries, including no-hit cases.
- Local retrieval/evaluation CLI, explicit optional JSON report export, and a
  loopback FastAPI API using the same core services.
- Deterministic schema-1 JSON evaluation reports with finite numeric output.
- Authored unit, negative-input, reproducibility, and interface-parity tests;
  an authored CI workflow for locked sync, Ruff checks, and pytest.
- Dataset rationales, metric definitions, architecture, contribution guidance,
  and private security-reporting guidance.
- Resolver-generated dependency lockfile and Docker build, test, and local API
  services; local suite and runtime verification completed on 2026-10-28.

### Limitations

- Retrieval only: no LLM answer generation, embeddings, live cloud integrations,
  or cloud resources are provisioned by the application.
- Small synthetic corpus with authored binary relevance labels. No real-world
  quality or security assurance is implied.
- ASCII token extraction is deliberately limited and is not multilingual word
  segmentation. BM25 scores are ranking signals, not calibrated confidence.
- Local tests passed; CI execution is pending. No quality claims or benchmark metric values may
  be made without executed tests/evaluation and relevance review.
- Maintainer approval was recorded on 2026-10-28; CI confirmation is pending. The
  API is experimental and intended for loopback use, not production hosting.

Release date approved by the maintainer: 2026-10-28. GitHub publication and CI
confirmation remain pending. No Git tag or GitHub release has been created.
