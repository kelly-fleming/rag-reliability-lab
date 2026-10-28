"""Static local documentation references; no CLI commands are executed."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_required_references_and_local_documentation_links():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for target in (
        "docs/DATASET.md",
        "docs/METRICS.md",
        "docs/ARCHITECTURE.md",
        "ROADMAP.md",
    ):
        assert f"]({target})" in readme
    documents = [
        ROOT / "README.md",
        ROOT / "ROADMAP.md",
        *sorted((ROOT / "docs").glob("*.md")),
    ]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            assert (document.parent / path).is_file(), (
                f"Missing link in {document.name}: {target}"
            )


def test_readme_documents_current_commands_and_verification_scope():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for command in (
        "uv sync --locked",
        "uv run --locked rag-lab retrieve",
        "uv run --locked rag-lab evaluate",
        "--host 127.0.0.1 --port 8000",
        "uv run --locked ruff check .",
        "uv run --locked ruff format --check .",
        "uv run --locked pytest -q",
    ):
        assert command in readme
    assert "retrieval-only" in readme
    assert "does not generate" in readme
    assert "Local tests and Docker runtime checks have passed" in readme
    assert "Maintainer approval is recorded; CI execution remains pending" in readme
