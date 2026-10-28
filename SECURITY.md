# Security

RAG Reliability Lab v0.1.0 is an experimental, non-production retrieval lab.
Input validation, safe error handling, and local-only application behavior have
passed automated verification. This does not establish production security
assurance. The project provides no production support or security response-time
guarantee.

The checked-in corpus and relevance judgments are fictional evaluation material.
The application has no live cloud integrations, provider accounts, remote search,
or LLM calls. It does not need API tokens to retrieve or evaluate local data.
Dependency installation and CI do download tools/packages; this is separate
from the local application data path. Do not add real customer information,
proprietary runbooks, credentials, or provider identifiers to fixtures or reports.

The HTTP API is intended for loopback use only. Follow the launch command in
[API documentation](docs/API.md), keeping it bound to `127.0.0.1`. It has no user
accounts or production access-control system. Do not expose it as a public
service or use it to host sensitive documents. CLI report export writes local
files only when explicitly requested; keep generated reports under `reports/`.

## Reporting a suspected vulnerability

Use the repository's private vulnerability reporting option on GitHub if it is
enabled. Otherwise use a private contact method explicitly published by the
repository owner. If neither is available, a public issue may request a private
reporting channel without revealing the vulnerability or sensitive information.
No private reporting channel or repository security setting is assumed enabled.

Privately include the affected commit, Python/dependency versions, minimal
reproduction steps using fictional data, expected/observed behavior, and the
potential impact. Redact tokens, personal data, host paths, and unrelated logs.
Do not paste exploit details or secrets into public issues or PRs. Reports are
reviewed on a best-effort basis; coordinate disclosure with the maintainer.

For ordinary bugs that contain no sensitive details, a focused public issue is
appropriate. Report observed behavior accurately: the lab treats document text
as data and does not claim to prevent arbitrary prompt injection in applications
that generate answers. See [metric limitations](docs/METRICS.md) and the
[operator validation process](docs/VALIDATION.md).
