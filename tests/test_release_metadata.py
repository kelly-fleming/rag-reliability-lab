"""Static release-version and documented capability consistency."""

import re
import tomllib
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_version_and_dated_release_notes_match():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    version = re.escape(metadata["project"]["version"])
    entries = re.findall(
        rf"^## {version} - (\d{{4}}-\d{{2}}-\d{{2}})\s*\n"
        r"(.*?)(?=^## |\Z)",
        changelog,
        re.MULTILINE | re.DOTALL,
    )
    assert len(entries) == 1, "Expected one changelog entry for the package version"
    release_date, release_notes = entries[0]
    date.fromisoformat(release_date)
    assert "### Added" in release_notes
    assert "### Limitations" in release_notes
    readme_release = re.search(rf"\b{version} - (\d{{4}}-\d{{2}}-\d{{2}})\b", readme)
    assert readme_release, "README must document the package version and release date"
    assert readme_release.group(1) == release_date
    assert "](CHANGELOG.md)" in readme


def test_readme_and_changelog_do_not_claim_future_capabilities_are_shipped():
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    changelog = " ".join((ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split())
    assert "retrieval-only" in readme
    assert "it does not generate answers or measure answer grounding" in readme
    assert "no LLM answer generation, embeddings, live cloud integrations" in changelog
    assert "No quality claims or benchmark metric values" in changelog
