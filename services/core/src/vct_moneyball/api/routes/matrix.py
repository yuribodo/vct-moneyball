"""GET /enc/matrix — pairwise win-probability matrix for all 16 ENC teams.

The engine behind the bracket + simulator. Trains the bridge model ONCE and replays player
ratings ONCE, then emits every pairwise probability — ~1s total versus ~15 sequential
``/enc/predict`` calls. Teams are ordered by the published roster ranking (the bracket seed).
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from vct_moneyball.api.artifacts import load_ranking
from vct_moneyball.api.deps import get_session
from vct_moneyball.api.schemas import MatrixResponse, MatrixTeam, Provenance
from vct_moneyball.bridge.features import matchup_features
from vct_moneyball.bridge.model import resolve_team, team_views_as_of, train_bridge
from vct_moneyball.bridge.player_rating import PlayerRatingConfig
from vct_moneyball.common.logging import CliError

router = APIRouter()

_LOOKBACK_MONTHS = 12


@router.get("/enc/matrix", response_model=MatrixResponse)
def matrix(
    as_of: str | None = None,
    aggregation: str = "mean",
    session: Session = Depends(get_session),
) -> MatrixResponse:
    if as_of is None:
        as_of_dt = datetime.now(UTC)
    else:
        try:
            as_of_dt = datetime.fromisoformat(as_of)
            if as_of_dt.tzinfo is None:
                as_of_dt = as_of_dt.replace(tzinfo=UTC)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"malformed as_of date: {exc}") from exc

    # Seed order + per-team confidence come from the published roster ranking.
    ranking = load_ranking(source="roster")
    seeded = sorted(ranking["teams"], key=lambda t: t["position"])

    # Country lookup from the power artifact (best-effort).
    countries: dict[str, str] = {}
    try:
        power = load_ranking(source="power")
        for t in power["teams"]:
            if t.get("country"):
                countries[str(t["team"]).casefold()] = t["country"]
    except HTTPException:
        pass

    cfg = PlayerRatingConfig()
    try:
        resolved = [(resolve_team(session, t["team"]), t) for t in seeded]
    except CliError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ids = [rid for (rid, _name), _t in resolved]

    model = train_bridge(
        session,
        as_of=as_of_dt,
        lookback_months=_LOOKBACK_MONTHS,
        cfg=cfg,
        aggregation=aggregation,
    )
    views = team_views_as_of(
        session,
        ids,
        as_of=as_of_dt,
        lookback_months=_LOOKBACK_MONTHS,
        cfg=cfg,
        aggregation=aggregation,
    )

    teams: list[MatrixTeam] = []
    strengths = []
    for (tid, _name), t in resolved:
        v = views[tid]
        strengths.append(v.strength)
        teams.append(
            MatrixTeam(
                team=t["team"],
                position=t["position"],
                elo=round(v.strength.elo, 1),
                confidence=t["confidence"],
                contributors=[h for h, _ in v.contributors[:3]],
                country=countries.get(str(t["team"]).casefold()),
            )
        )

    n = len(strengths)
    p: list[list[float]] = [[0.5] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            p[i][j] = round(model.predict_proba_a(matchup_features(strengths[i], strengths[j])), 4)

    return MatrixResponse(
        as_of=as_of_dt.isoformat(),
        aggregation=aggregation,
        teams=teams,
        p=p,
        provenance=Provenance(source="model_run", as_of=as_of_dt.isoformat()),
    )
