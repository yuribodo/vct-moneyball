"""SQLAlchemy 2.0 engine and session factory (psycopg 3 driver).

The connection string comes from ``DATABASE_URL`` (see ``.env.example``). Postgres is
the system of record (Constitution I); this module is the single place that builds the
engine so tests and the CLI share one configuration path.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from vct_moneyball.common.logging import CliError

_DEFAULT_URL = "postgresql+psycopg://vct:vct@localhost:5432/vct_moneyball"


def database_url() -> str:
    """Resolve the database URL from the environment (``.env`` honored)."""
    load_dotenv()
    return os.environ.get("DATABASE_URL", _DEFAULT_URL)


def make_engine(url: str | None = None, *, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine for the resolved (or supplied) URL."""
    return create_engine(url or database_url(), echo=echo, future=True, pool_pre_ping=True)


def make_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Return a configured ``sessionmaker`` bound to ``engine``."""
    return sessionmaker(bind=engine or make_engine(), expire_on_commit=False, future=True)


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Transactional scope: commit on success, roll back on error, always close."""
    factory = make_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_connectivity(engine: Engine | None = None) -> None:
    """Raise :class:`CliError` if the database cannot be reached."""
    from sqlalchemy import text

    eng = engine or make_engine()
    try:
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover - exercised via CLI
        raise CliError(f"cannot reach database at {eng.url!r}: {exc}") from exc
