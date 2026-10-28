"""Fixed expectations for the shared v0.1.0 tokenization contract."""

import pytest

from rag_reliability_lab.tokenize import tokenize


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("BACKUP Retention", ("backup", "retention")),
        (" \tworker\n\r backlog  ", ("worker", "backlog")),
        (
            "queue-age,error_count: (retry)!",
            ("queue", "age", "error", "count", "retry"),
        ),
        (
            "us-east-1 i-0abc123 s3://demo-bucket",
            ("us", "east", "1", "i", "0abc123", "s3", "demo", "bucket"),
        ),
        ("Retry RETRY retry", ("retry", "retry", "retry")),
        ("The workers are running", ("the", "workers", "are", "running")),
        ("", ()),
        (" \n\t", ()),
        ("---...!?", ()),
        ("café naïve Straße", ("caf", "na", "ve", "stra", "e")),
        ("中文 日本語 １２３", ()),
        ("K İ", ("k", "i")),
    ],
)
def test_exact_tokens(text, expected):
    assert tokenize(text) == expected
    assert tokenize(text) == expected
