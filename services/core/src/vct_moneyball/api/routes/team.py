"""GET /enc/team/{name} — rich per-team detail, merged from published artifacts.

Reads the power ranking (contributors + per-map breakdown + country) and the roster
ranking (Elo + the live ranking position) byte-faithfully and merges them by team name.
No DB access — these are frozen artifacts (Constitution II).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from vct_moneyball.api.artifacts import load_ranking
from vct_moneyball.api.schemas import (
    Provenance,
    TeamContributor,
    TeamDetailResponse,
    TeamMapScore,
)

router = APIRouter()


def _find(teams: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    needle = name.strip().casefold()
    for t in teams:
        if str(t.get("team", "")).casefold() == needle:
            return t
    return None


@router.get("/enc/team/{name}", response_model=TeamDetailResponse)
def team(name: str, version: str | None = None) -> TeamDetailResponse:
    power = load_ranking(source="power", version=version)
    pt = _find(power["teams"], name)
    if pt is None:
        raise HTTPException(status_code=404, detail=f"team {name!r} not found")

    # Roster ranking is the live published ranking — its position + Elo win.
    roster_pos = pt["position"]
    roster_elo: float | None = None
    confidence = pt["confidence"]
    try:
        roster = load_ranking(source="roster")
        rt = _find(roster["teams"], name)
        if rt is not None:
            roster_pos = rt.get("position", roster_pos)
            roster_elo = rt.get("roster_elo")
            confidence = rt.get("confidence", confidence)
    except HTTPException:
        pass  # roster artifact optional — fall back to power values

    contributors = [
        TeamContributor(
            player=c["player"],
            player_score=float(c["player_score"]),
            maps_played=int(c["maps_played"]),
            confidence=c["confidence"],
            low_history_baseline=bool(c["low_history_baseline"]),
        )
        for c in pt.get("contributors", [])
    ]
    map_breakdown = [
        TeamMapScore(
            map=m["map"],
            map_score=float(m["map_score"]),
            confidence=m["confidence"],
        )
        for m in pt.get("map_breakdown", [])
    ]

    return TeamDetailResponse(
        team=pt["team"],
        country=pt.get("country"),
        position=roster_pos,
        team_score=float(pt["team_score"]),
        roster_elo=roster_elo,
        confidence=confidence,
        contributors=contributors,
        map_breakdown=map_breakdown,
        provenance=Provenance(source="artifact", version=power["version"]),
    )
