"""Read and validate local fixtures without writing files.

The default directory is relative to the working directory, not package resources.
Strings are stripped at their outer edges; internal text is preserved. Records
and collection members retain fixture order. Error messages identify schema
locations without echoing paths, field names supplied by users, or file contents.
"""

import json
import re
from pathlib import Path

from rag_reliability_lab.models import Document, EvaluationQuery


class DatasetError(ValueError):
    """A safe, expected failure reading or validating a fixture dataset."""


def _object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DatasetError("Fixture JSON contains a duplicate object field.")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise DatasetError("Fixture JSON contains a nonstandard numeric constant.")


def _read_records(data_dir: Path | str, filename: str) -> list[object]:
    try:
        path = Path(data_dir) / filename
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError, TypeError, ValueError):
        raise DatasetError(f"Cannot read {filename} as UTF-8.") from None
    try:
        records = json.loads(
            text, object_pairs_hook=_object, parse_constant=_reject_constant
        )
    except DatasetError:
        raise
    except (ValueError, RecursionError):
        raise DatasetError(f"Invalid JSON in {filename}.") from None
    if not isinstance(records, list):
        raise DatasetError(f"{filename} must contain a JSON array.")
    if not records:
        raise DatasetError(f"{filename} must contain at least one record.")
    return records


def _record(value: object, fields: set[str], location: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise DatasetError(
            f"{location} must be an object with exactly the required fields."
        )
    return value


def _text(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DatasetError(f"{location} must be a nonempty string.")
    return value.strip()


def _identifier(value: object, prefix: str, location: str) -> str:
    identifier = _text(value, location)
    if re.fullmatch(rf"{prefix}-[0-9]{{3}}", identifier) is None:
        raise DatasetError(f"{location} must have format {prefix}-NNN.")
    return identifier


def _strings(value: object, location: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise DatasetError(f"{location} must be an array of strings.")
    return tuple(
        _text(item, f"{location}[{index}]") for index, item in enumerate(value)
    )


def load_documents(data_dir: Path | str = Path("data")) -> tuple[Document, ...]:
    """Load documents.json alone, so retrieval needs no relevance fixture."""
    records = _read_records(data_dir, "documents.json")
    documents = []
    seen = set()
    for index, value in enumerate(records):
        location = f"documents[{index}]"
        record = _record(value, {"id", "title", "body", "tags"}, location)
        identifier = _identifier(record["id"], "doc", f"{location}.id")
        if identifier in seen:
            raise DatasetError(f"{location}.id duplicates an earlier document ID.")
        seen.add(identifier)
        documents.append(
            Document(
                id=identifier,
                title=_text(record["title"], f"{location}.title"),
                body=_text(record["body"], f"{location}.body"),
                tags=_strings(record["tags"], f"{location}.tags"),
            )
        )
    return tuple(documents)


def load_dataset(
    data_dir: Path | str = Path("data"),
) -> tuple[tuple[Document, ...], tuple[EvaluationQuery, ...]]:
    """Load documents and evaluation_queries.json, validating gold references."""
    documents = load_documents(data_dir)
    known_ids = {document.id for document in documents}
    records = _read_records(data_dir, "evaluation_queries.json")
    queries = []
    seen = set()
    for index, value in enumerate(records):
        location = f"queries[{index}]"
        record = _record(value, {"id", "question", "relevant_document_ids"}, location)
        identifier = _identifier(record["id"], "q", f"{location}.id")
        if identifier in seen:
            raise DatasetError(f"{location}.id duplicates an earlier query ID.")
        seen.add(identifier)
        question = _text(record["question"], f"{location}.question")
        relevant = _strings(
            record["relevant_document_ids"], f"{location}.relevant_document_ids"
        )
        if not relevant:
            raise DatasetError(f"{location}.relevant_document_ids must not be empty.")
        if len(set(relevant)) != len(relevant):
            raise DatasetError(
                f"{location}.relevant_document_ids contains duplicate IDs."
            )
        for member_index, member in enumerate(relevant):
            _identifier(
                member, "doc", f"{location}.relevant_document_ids[{member_index}]"
            )
            if member not in known_ids:
                raise DatasetError(
                    f"{location}.relevant_document_ids references an unknown document."
                )
        queries.append(EvaluationQuery(identifier, question, relevant))
    return documents, tuple(queries)
