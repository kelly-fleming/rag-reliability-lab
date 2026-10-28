# Operator validation

Local verification on 2026-10-28 passed the test suite in Docker,
plus Docker API/CLI smoke checks. The resolver-generated `uv.lock` is included.
Maintainer approval is recorded on 2026-10-28; CI execution at the eventual commit
remains pending. No performance or real-world benchmark claims follow from these checks.

From the repository root, with uv installed, the final operator runs:

```bash
uv python install 3.12
uv sync --locked
uv run --locked python -c "import rag_reliability_lab"
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked pytest -q
```

For dependency updates, run `uv lock` and review its resolver output. Commit `uv.lock` alongside
the reviewed implementation. Do not commit virtual environments, reports,
secrets, or caches. If checks fail, fix the actual failures and rerun the checks;
do not weaken assertions, suppress failures, or claim an unexecuted check passed.

Then exercise the CLI and local API, inspect the authored relevance judgments,
and hand-check metric denominators, including no-hit queries:

```bash
uv run --locked rag-lab retrieve --query "backup retention" --k 5
uv run --locked rag-lab evaluate --k 5
uv run --locked uvicorn rag_reliability_lab.api:app --host 127.0.0.1 --port 8000
```

Keep the server bound to loopback. In another terminal use the payloads in
[API.md](API.md) to inspect `/health`, `/retrieve`, `/evaluate`, and `/docs`.
The full operator publication checklist is in
[HUMAN_VERIFICATION.md](../HUMAN_VERIFICATION.md); these are future operator
actions, not actions performed while authoring this workflow.

After local verification and lockfile commit, the operator pushes a branch and
opens a PR. The `CI` workflow runs the `checks` job on push and pull requests,
using read-only repository permissions and cancelling superseded runs for the
same workflow/ref. Confirm a successful run at the exact PR commit before
enabling required status checks or publishing. Record actual commands, commit,
and results in the local verification record.

Action references are pinned to these upstream releases/commits:

- [actions/checkout v4.2.2](https://github.com/actions/checkout/releases/tag/v4.2.2),
  commit `11bd71901bbe5b1630ceea73d27597364c9af683`.
- [astral-sh/setup-uv v6.0.1](https://github.com/astral-sh/setup-uv/releases/tag/v6.0.1),
  commit `6b9c6063abd6010835644d4c2e1bef4cf5cd0fca`.

Review upstream changes explicitly when updating action pins. No green badge or
passing CI claim is supplied by this document.
