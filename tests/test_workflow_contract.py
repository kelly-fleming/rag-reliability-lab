"""Static workflow text contracts; do not run CI or require a lockfile."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_triggers_permissions_and_job():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert re.search(r"^name: CI$", workflow, re.MULTILINE)
    assert re.search(r"^on:\n  push:\n  pull_request:", workflow, re.MULTILINE)
    assert re.search(r"^permissions:\n  contents: read$", workflow, re.MULTILINE)
    assert "write" not in workflow
    assert "group: ${{ github.workflow }}-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow
    assert re.search(
        r"^jobs:\n  checks:\n    runs-on: ubuntu-latest$", workflow, re.MULTILINE
    )
    assert "continue-on-error" not in workflow
    assert "|| true" not in workflow


def test_ci_action_pins_and_required_commands():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    pins = re.findall(r"uses: ([\w/-]+)@([0-9a-f]{40})(?:\s|$)", workflow)
    assert {action for action, _ in pins} == {"actions/checkout", "astral-sh/setup-uv"}
    assert len(pins) == 2
    commands = re.findall(r"^\s+run: (.+)$", workflow, re.MULTILINE)
    assert commands == [
        "uv python install 3.12",
        "uv sync --locked",
        "uv run --locked ruff check .",
        "uv run --locked ruff format --check .",
        "uv run --locked pytest -q",
    ]
    assert "persist-credentials: false" in workflow
