"""Read-only dependencies: a DB session and a liveness check.

The session is for reads only; no route writes. Built from the same ``make_engine`` the CLI
uses, so the API and CLI share one configuration path.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from vct_moneyball.store.db import make_engine


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    return make_engine()


def get_session() -> Iterator[Session]:
    """FastAPI dependency: a session closed after the request (read-only use)."""
    session = Session(bind=get_engine())
    try:
        yield session
    finally:
        session.close()


def database_status() -> str:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"
