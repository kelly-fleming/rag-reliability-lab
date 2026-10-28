"""Check declared metadata without building or importing the application."""

import ast
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_metadata():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]

    assert project["name"] == "rag-reliability-lab"
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.12"
    assert project["scripts"] == {"rag-lab": "rag_reliability_lab.cli:main"}
    assert metadata["build-system"]["build-backend"] == "hatchling.build"
    assert any(
        requirement.startswith("hatchling>=")
        for requirement in metadata["build-system"]["requires"]
    )
    assert metadata["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == [
        "src/rag_reliability_lab"
    ]


def test_dependencies_and_tool_configuration():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_names = {
        requirement.split(">=")[0]
        for requirement in metadata["project"]["dependencies"]
    }
    dev_names = {
        requirement.split(">=")[0]
        for requirement in metadata["dependency-groups"]["dev"]
    }

    assert {"fastapi", "uvicorn"} <= runtime_names
    assert {"pytest", "httpx", "ruff"} <= dev_names
    assert metadata["tool"]["pytest"]["ini_options"]["testpaths"] == ["tests"]
    assert metadata["tool"]["ruff"]["target-version"] == "py312"
    assert "F" in metadata["tool"]["ruff"]["lint"]["select"]
    assert metadata["tool"]["ruff"]["format"]["line-ending"] == "lf"
    assert (ROOT / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
    assert "charset = utf-8" in (ROOT / ".editorconfig").read_text(encoding="utf-8")


def test_source_version_matches_distribution_metadata():
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    source = ROOT / "src" / "rag_reliability_lab" / "__init__.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    versions = [
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in node.targets
        )
    ]
    assert versions == [metadata["project"]["version"]]
