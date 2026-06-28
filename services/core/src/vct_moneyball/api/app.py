"""FastAPI app factory for the read-only ENC prediction API.

Composes the existing pipeline behind a thin HTTP surface: it serves published artifacts
(rankings, eval reports) and live predictions (via the feature-003 bridge). Exceptions map to
honest status codes with a consistent ``ErrorResponse`` body — never a misleading 200 or an
unhandled 500 (FR-007).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from vct_moneyball.api.routes import evaluation, health, predict, ranking
from vct_moneyball.common.logging import CliError


def create_app() -> FastAPI:
    app = FastAPI(
        title="ENC Prediction API",
        version="0.1.0",
        summary="Read-only serving of ENC rankings, predictions, and honest evaluations.",
    )

    @app.exception_handler(HTTPException)
    async def _http_error(_: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": str(exc.detail), "status": exc.status_code},
        )

    @app.exception_handler(CliError)
    async def _cli_error(_: Request, exc: CliError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(exc), "status": 400})

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Surface dependency failures as 503 rather than a leaking 500.
        return JSONResponse(
            status_code=503,
            content={"error": f"service unavailable: {exc}", "status": 503},
        )

    app.include_router(health.router)
    app.include_router(ranking.router)
    app.include_router(predict.router)
    app.include_router(evaluation.router)
    return app


app = create_app()
