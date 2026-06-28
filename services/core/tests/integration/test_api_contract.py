"""T014 — read-only guarantee + consistent error-model shape."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.seed import seed_attributed_matches
from vct_moneyball.api.app import create_app
from vct_moneyball.store.models import Match, PlayerMapStat


def _counts(engine):
    with Session(engine) as s:
        return (
            s.execute(select(func.count()).select_from(Match)).scalar_one(),
            s.execute(select(func.count()).select_from(PlayerMapStat)).scalar_one(),
        )


pytestmark = pytest.mark.integration


def test_requests_do_not_mutate_data(clean_db) -> None:
    with Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=160)
        s.commit()
    before = _counts(clean_db)
    client = TestClient(create_app())
    client.get("/health")
    client.get("/enc/predict?team_a=BTeam15&team_b=BTeam00&as_of=2026-11-08")
    client.get("/enc/ranking")  # 404 (no artifact) — still read-only
    assert _counts(clean_db) == before  # nothing written


def test_error_response_shape() -> None:
    r = TestClient(create_app()).get("/enc/predict?team_a=A&team_b=B&as_of=bad")
    assert r.status_code == 400
    body = r.json()
    assert set(body) == {"error", "status"} and body["status"] == 400
