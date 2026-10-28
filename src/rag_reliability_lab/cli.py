"""Local command-line adapters; importing this module performs no operations."""

import argparse
import json
import sys
from pathlib import Path

from rag_reliability_lab.dataset import DatasetError, load_dataset, load_documents
from rag_reliability_lab.evaluation import EvaluationError, evaluate
from rag_reliability_lab.reporting import ReportingError, serialize_report
from rag_reliability_lab.retrieval import RetrievalError, retrieve


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-lab",
        description="Local retrieval over fictional cloud operations data.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    retrieval = commands.add_parser(
        "retrieve", help="Return ranked document IDs and scores"
    )
    retrieval.add_argument(
        "--query", required=True, help="Nonblank query, at most 500 characters"
    )
    retrieval.add_argument(
        "--k", type=int, default=5, help="Maximum hits, integer 1..20 (default: 5)"
    )
    retrieval.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Fixture directory relative to the working directory (default: ./data)",
    )
    evaluation = commands.add_parser("evaluate", help="Evaluate all authored queries")
    evaluation.add_argument(
        "--k", type=int, default=5, help="Metric cutoff, integer 1..20"
    )
    evaluation.add_argument("--data-dir", type=Path, default=Path("data"))
    evaluation.add_argument(
        "--output", type=Path, help="Explicit UTF-8 report destination"
    )
    evaluation.add_argument(
        "--overwrite", action="store_true", help="Allow replacing an existing report"
    )
    return parser


class _OutputError(ValueError):
    """Safe report destination failure."""


def _write_report(output: Path, text: str, data_dir: Path, overwrite: bool) -> None:
    try:
        destination = output.resolve()
        fixture_dirs = (
            data_dir,
            Path.cwd() / "data",
            Path(__file__).resolve().parents[2] / "data",
        )
        for directory in fixture_dirs:
            for filename in ("documents.json", "evaluation_queries.json"):
                fixture = directory / filename
                if destination == fixture.resolve() or (
                    output.exists() and fixture.exists() and output.samefile(fixture)
                ):
                    raise _OutputError(
                        "Report output must not replace dataset fixtures."
                    )
        # Do not follow symlinks when replacing an existing report.
        if output.is_symlink():
            raise _OutputError("Report output must not be a symbolic link.")
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            stream = output.open(
                "w" if overwrite else "x", encoding="utf-8", newline="\n"
            )
        except FileExistsError:
            raise _OutputError(
                "Report output already exists; use --overwrite to replace it."
            ) from None
        with stream:
            stream.write(text)
    except _OutputError:
        raise
    except (OSError, ValueError, RuntimeError):
        raise _OutputError("Cannot write report output.") from None


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return 0 on success, 1 on operation errors, 2 on usage errors.

    argv=None reads process arguments. Help returns 0. Expected parse failures
    return argparse's status without escaping as SystemExit to direct callers.
    """
    parser = _parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)

    if args.command == "evaluate" and args.overwrite and args.output is None:
        print("rag-lab: --overwrite requires --output.", file=sys.stderr)
        return 2
    try:
        if args.command == "retrieve":
            documents = load_documents(args.data_dir)
            results = retrieve(documents, args.query, k=args.k)
            output = (
                json.dumps(results, sort_keys=True, indent=2, allow_nan=False) + "\n"
            )
        else:
            documents, queries = load_dataset(args.data_dir)
            output = serialize_report(evaluate(documents, queries, k=args.k))
            if args.output is not None:
                _write_report(args.output, output, args.data_dir, args.overwrite)
                return 0
    except (
        DatasetError,
        RetrievalError,
        EvaluationError,
        ReportingError,
        _OutputError,
    ) as error:
        print(f"rag-lab: {error}", file=sys.stderr)
        return 1

    try:
        print(output, end="")
    except OSError:
        print("rag-lab: Cannot write JSON to stdout.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
