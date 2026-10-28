# Contributing

Keep contributions focused on the local retrieval/evaluation scope described in
[README.md](README.md) and [ARCHITECTURE.md](docs/ARCHITECTURE.md). Discuss changes
to evaluation semantics or new external dependencies before expanding the scope.
Do not add proprietary material, personal information, real customer names,
provider account IDs, secrets, or copied internal runbooks. Author fictional
examples and keep relevance labels independent of ranking outputs.

## Development workflow

Use Python 3.12 and uv from the repository root with the included resolver-generated
`uv.lock`. Docker equivalents are in [README.md](README.md).

```bash
uv python install 3.12
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

For a dependency change, the operator runs `uv lock`, reviews the genuine
resolver changes, commits `pyproject.toml` and `uv.lock` together, and repeats
locked installation and checks. Follow [API.md](docs/API.md) for loopback-only
manual endpoint checks. Record actual check results. Report quality scores from
executed evaluation with reviewed gold judgments.

## Code, data, and tests

- Use snake_case Python modules/functions and `test_*.py` test files; keep UTF-8
  source and the repository's Ruff configuration.
- Preserve stable document/query IDs when editing fixtures. Update independently
  reasoned relevance rationales when meanings change; do not rewrite gold labels
  to fit predictions.
- Keep imports free of operational work. Share core parsing, retrieval, metrics,
  and serialization between interfaces rather than duplicating semantics.
- Add regression cases with behavior changes, including relevant invalid inputs.
  Use temporary files and fixed expected ranks/fractions rather than calculating
  expected results with the same function being tested. Tests must not depend on
  external services or modify source fixtures.
- Keep `.venv/`, caches, `reports/`, and generated outputs out of commits.
  `uv.lock` and fictional source fixtures belong in version control. The current
  application needs no tokens; if local tooling requires them, keep them in an
  ignored `.env`, `.secrets/`, `.tokens/`, or `.api-token` file, never source code.
  Ignore rules do not remove files already tracked, so inspect staged changes.

## Pull requests

Use a focused conventional title such as `fix: preserve the metric cutoff` or
`docs: clarify local setup`. Explain the concrete behavior change, its reason,
and exactly which checks ran or did not run. Preserve unrelated work and avoid
mixing generated reports, broad refactors, and feature changes into one PR.

Run the test suite, lint, and formatting checks for changes. Fix failures without
weakening assertions or suppressing checks. Keep release documentation focused
on implemented behavior and completed verification, with substantive limitations
intact.

Follow [SECURITY.md](SECURITY.md) for sensitive reports. The existing
[MIT license](LICENSE) is retained; contribute material you are entitled to
share under that license.
