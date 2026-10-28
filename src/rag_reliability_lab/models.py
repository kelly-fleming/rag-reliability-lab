"""Immutable core values; construction performs no I/O."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Document:
    id: str
    title: str
    body: str
    tags: tuple[str, ...]

    def __post_init__(self) -> None:
        # Own the collection even when a caller supplied a mutable sequence.
        object.__setattr__(self, "tags", tuple(self.tags))


@dataclass(frozen=True, slots=True)
class EvaluationQuery:
    id: str
    question: str
    relevant_document_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "relevant_document_ids", tuple(self.relevant_document_ids)
        )
