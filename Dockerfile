FROM ghcr.io/astral-sh/uv:0.11.19 AS uv
FROM python:3.12-slim AS base
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable
COPY data ./data
ENV PATH="/app/.venv/bin:$PATH"

FROM base AS test
RUN uv sync --locked --no-editable
COPY . .
CMD ["pytest", "-q"]

FROM base AS runtime
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["uvicorn", "rag_reliability_lab.api:app", "--host", "0.0.0.0", "--port", "8000"]
