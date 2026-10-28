"""Static release-version and documented capability consistency."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_version_and_dated_release_notes_match():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert metadata["project"]["version"] == "0.1.0"
    assert "## 0.1.0 - 2026-10-28" in changelog
    assert "### Added" in changelog
    assert "### Limitations" in changelog
    assert "**0.1.0 - 2026-10-28**" in readme
    assert "](CHANGELOG.md)" in readme


def test_readme_and_roadmap_do_not_claim_future_capabilities_are_shipped():
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    roadmap = " ".join((ROOT / "ROADMAP.md").read_text(encoding="utf-8").split())
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split())
    assert "retrieval-only" in readme
    assert "it does not generate answers or measure answer grounding" in readme
    assert "Local tests and Docker runtime checks have passed" in readme
    assert "Maintainer approval is recorded; CI execution remains pending" in readme
    assert (
        "Answer generation, embeddings, and live cloud integration are outside "
        "the current implementation"
    ) in roadmap
    assert "Future versions require separately scoped work" in roadmap
    assert "no LLM answer generation, embeddings, live cloud integrations" in changelog
    assert "No quality claims or benchmark metric values" in changelog
