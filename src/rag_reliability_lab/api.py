"""Local read-only HTTP adapters; see docs/API.md for localhost launch details."""

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

from rag_reliability_lab.dataset import DatasetError, load_dataset, load_documents
from rag_reliability_lab.evaluation import EvaluationError, evaluate
from rag_reliability_lab.reporting import ReportingError, serialize_report
from rag_reliability_lab.retrieval import RetrievalError, retrieve

Limit = Annotated[int, Field(strict=True, ge=1, le=20)]


class RetrieveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: Annotated[str, Field(strict=True, min_length=1, max_length=500)]
    k: Limit = 5

    @field_validator("query")
    @classmethod
    def nonblank_query(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Query must not be blank.")
        return value


class EvaluateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    k: Limit = 5


def create_app(data_dir: Path | None = None) -> FastAPI:
    """Construct without reading fixtures; resolve server configuration once.

    Bind the ASGI server to 127.0.0.1 as documented. Request bodies cannot choose
    paths. Health is process liveness, not an assertion of valid fixture data.
    """
    directory = (Path("data") if data_dir is None else Path(data_dir)).absolute()
    application = FastAPI(
        title="RAG Reliability Lab",
        version="0.1.0",
        description="Local retrieval-only experiments over fictional cloud operations data.",
        debug=False,
    )

    @application.exception_handler(RequestValidationError)
    async def invalid_request(
        request: Request, error: RequestValidationError
    ) -> JSONResponse:
        # Default validation details include supplied inputs; keep errors safe.
        return JSONResponse(
            status_code=422, content={"detail": "Invalid request payload."}
        )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/retrieve")
    def retrieve_endpoint(payload: RetrieveRequest) -> JSONResponse:
        try:
            documents = load_documents(directory)
            results = retrieve(documents, payload.query, k=payload.k)
        except DatasetError:
            raise HTTPException(
                status_code=503, detail="Dataset is unavailable or invalid."
            ) from None
        except RetrievalError:
            raise HTTPException(
                status_code=422, detail="Cannot retrieve with the supplied inputs."
            ) from None
        return JSONResponse(content=results)

    @application.post("/evaluate")
    def evaluate_endpoint(payload: EvaluateRequest) -> Response:
        """Return the same deterministic schema-1 JSON text as CLI evaluation."""
        try:
            documents, queries = load_dataset(directory)
            report = serialize_report(evaluate(documents, queries, k=payload.k))
        except DatasetError:
            raise HTTPException(
                status_code=503, detail="Dataset is unavailable or invalid."
            ) from None
        except EvaluationError:
            raise HTTPException(
                status_code=422, detail="Cannot evaluate with the supplied inputs."
            ) from None
        except ReportingError:
            raise HTTPException(
                status_code=500, detail="Cannot serialize evaluation report."
            ) from None
        return Response(content=report, media_type="application/json")

    return application


app = create_app()
