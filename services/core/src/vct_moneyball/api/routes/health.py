"""GET /health — liveness + database reachability."""

from __future__ import annotations

from fastapi import APIRouter

from vct_moneyball.api.deps import database_status
from vct_moneyball.api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", database=database_status())
