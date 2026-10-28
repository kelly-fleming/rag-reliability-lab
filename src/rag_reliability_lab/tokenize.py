"""Shared, deliberately ASCII-only tokenization for indexing and queries."""

import re

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> tuple[str, ...]:
    """Lowercase text, then return ASCII alphanumeric runs in input order.

    Punctuation, underscores, and hyphens split tokens. Repeated tokens remain;
    there is no stemming or stopword filtering. This is not multilingual word
    segmentation: non-ASCII characters split or disappear rather than being
    transliterated. Python lowercasing runs first, so a Unicode character whose
    lowercase form contains ASCII (for example the Kelvin sign) may contribute
    ASCII tokens. No Unicode normalization or casefolding is performed.

    Index and query callers must use this same function for matching semantics.
    """
    return tuple(_TOKEN.findall(text.lower()))
