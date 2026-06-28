"""Shared test fixtures.

Integration tests run against a **dedicated** database (``<db>_test``, or
``TEST_DATABASE_URL`` if set) created and schema-built on demand, so they never touch
real collected data even though ``clean_db`` truncates tables. ``db_session`` wraps each
test in a rolled-back transaction. If Postgres is unreachable the fixtures skip (offline
unit tests still run).
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from vct_moneyball.store.db import database_url, make_engine
from vct_moneyball.store.models import Base


def _ensure_test_database():
    """Resolve (and create if needed) the isolated test database; return its engine."""
    test_url = os.environ.get("TEST_DATABASE_URL")
    url = make_url(test_url) if test_url else make_url(database_url())
    if not test_url:
        url = url.set(database=f"{url.database}_test")

    # Create the test DB if missing (connect to the admin 'postgres' database).
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()

    # Point the whole test process at the test DB so CLI handlers (which build their
    # own engine via make_engine()) stay isolated from real data too.
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    eng = make_engine()
    # Disposable test DB: rebuild the schema each session so it always matches the models
    # (create_all alone won't add columns to a pre-existing table).
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture(scope="session")
def engine():
    try:
        eng = _ensure_test_database()
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
