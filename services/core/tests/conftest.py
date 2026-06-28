"""Shared test fixtures.

``db_session`` yields a SQLAlchemy session bound to a single connection wrapped in an
outer transaction that is rolled back after each test, so integration tests share the
migrated schema without leaving data behind. If Postgres is unreachable the fixture
skips (offline unit tests still run).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from vct_moneyball.store.db import make_engine


@pytest.fixture(scope="session")
def engine():
    eng = make_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - depends on environment
        pytest.skip(f"database unavailable: {exc}")
    return eng


@pytest.fixture
def db_session(engine) -> Iterator[Session]:
    connection = engine.connect()
    trans = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()


_ALL_TABLES = (
    "outcome_comparison, ranking_map_breakdown, ranking_entry, ranking, "
    "player_map_stat, match_map, match, team_player, player, team, map"
)


def _truncate_all(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_ALL_TABLES} RESTART IDENTITY CASCADE"))


@pytest.fixture
def clean_db(engine):
    """Empty all domain tables before and after a test that commits to the real DB."""
    _truncate_all(engine)
    try:
        yield engine
    finally:
        _truncate_all(engine)
