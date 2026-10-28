# Local HTTP API

The API exposes retrieval and evaluation over fictional local fixtures. It does
not generate answers, require credentials, or create cloud resources. After the
operator has generated the genuine dependency lockfile and installed dependencies,
launch it on the loopback interface only:

```bash
uv run --locked uvicorn rag_reliability_lab.api:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for generated input documentation. Do not bind
this development API to a public interface. No permissive CORS policy is added.

- `GET /health` returns `{"status":"ok"}` without reading fixtures. This is
  process liveness; it does not certify dataset readiness.
- `POST /retrieve` accepts `{"query":"backup retention","k":5}` and returns the
  same array of document_id/title/rank/score objects as CLI retrieval. No-match
  queries return `[]`; full document bodies are omitted.
- `POST /evaluate` accepts `{"k":5}` and returns the same deterministic schema-1
  JSON text as CLI evaluation, documented in `reporting.py`. `{}` uses k=5.

Both POST routes require a JSON object. k defaults to 5 and must be an integer
from 1 through 20; booleans, strings, and floats are rejected. Queries must be
nonblank strings with at most 500 supplied characters before whitespace stripping.
Extra fields are rejected. The data directory is server configuration only:
`create_app(data_dir=Path(...))` selects it, otherwise `./data` is anchored to the
server's working directory when the app is created. Payloads cannot select paths.

Invalid payloads/core input failures return 422; unavailable or invalid fixtures
return 503; serialization failures return 500. Error bodies omit internal paths,
input contents, and tracebacks. There are no data write endpoints or export route.
Fixture reads and evaluation occur only on explicit requests, not on import.

These commands and endpoints have been authored but not executed or verified.
