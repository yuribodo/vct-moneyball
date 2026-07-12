"""GET /enc/ranking — serve the latest published ENC ranking, byte-faithful."""

from __future__ import annotations

from fastapi import APIRouter

from vct_moneyball.api.artifacts import load_ranking
from vct_moneyball.api.schemas import Provenance, RankingResponse, RankingTeam

router = APIRouter()


@router.get("/enc/ranking", response_model=RankingResponse)
def ranking(source: str = "roster", version: str | None = None) -> RankingResponse:
    data = load_ranking(source=source, version=version)
    as_of = data.get("as_of") or data.get("published_at")
    teams = [
        RankingTeam(
            position=t["position"],
            team=t["team"],
            score=float(t.get("roster_elo", t.get("team_score", 0.0))),
            confidence=t["confidence"],
            elo_margin_to_next=t.get("elo_margin_to_next"),
            separation=t.get("separation"),
        )
        for t in data["teams"]
    ]
    return RankingResponse(
        version=data["version"],
        as_of=as_of,
        aggregation=data.get("aggregation"),
        teams=teams,
        provenance=Provenance(source="artifact", version=data["version"], as_of=as_of),
    )
