"""GET /enc/predict — live ENC matchup prediction (CLI-parity via the bridge)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vct_moneyball.api.deps import get_session
from vct_moneyball.api.schemas import PredictionResponse, Provenance
from vct_moneyball.bridge.model import predict_matchup
from vct_moneyball.common.logging import CliError

router = APIRouter()


@router.get("/enc/predict", response_model=PredictionResponse)
def predict(
    team_a: str,
    team_b: str,
    as_of: str | None = None,
    aggregation: str = "mean",
    session: Session = Depends(get_session),
) -> PredictionResponse:
    if as_of is None:
        as_of_dt = datetime.now(UTC)
    else:
        try:
            as_of_dt = datetime.fromisoformat(as_of)
            if as_of_dt.tzinfo is None:
                as_of_dt = as_of_dt.replace(tzinfo=UTC)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"malformed as_of date: {exc}") from exc

    try:
        pred = predict_matchup(session, team_a, team_b, as_of=as_of_dt, aggregation=aggregation)
    except CliError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PredictionResponse(
        team_a=pred.team_a,
        team_b=pred.team_b,
        as_of=as_of_dt.isoformat(),
        p_a=round(pred.p_a, 4),
        p_b=round(pred.p_b, 4),
        winner=pred.winner,
        low_confidence=pred.low_confidence,
        elo_a=round(pred.elo_a, 1),
        elo_b=round(pred.elo_b, 1),
        contributors_a=pred.contributors_a,
        contributors_b=pred.contributors_b,
        provenance=Provenance(source="model_run", as_of=as_of_dt.isoformat()),
    )
