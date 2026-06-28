"""SQLAlchemy 2.0 ORM models — the Postgres system of record.

Schema mirrors ``specs/001-enc-power-ranking/data-model.md`` exactly: surrogate
identity PKs, ``numeric`` for stored stats (never float), natural keys as ``UNIQUE``
constraints, FKs with explicit ``ON DELETE``, indexes on every FK and filter column,
and provenance columns (``source_url`` + ``captured_at``) on every collected row
(Constitution I).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all models."""


def _pk() -> Mapped[int]:
    return mapped_column(BigInteger, primary_key=True, autoincrement=True)


# --------------------------------------------------------------------------- #
# Collected entities (carry provenance)                                       #
# --------------------------------------------------------------------------- #
class Team(Base):
    __tablename__ = "team"

    id: Mapped[int] = _pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    # NULL for non-ENC clubs (backfilled opponents); Postgres treats NULLs as distinct in
    # uq_team_name_country, so same-named clubs with different VLR ids never collide.
    country: Mapped[str | None] = mapped_column(Text, nullable=True)
    vlr_team_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_enc_2026: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("name", "country", name="uq_team_name_country"),
        UniqueConstraint("vlr_team_id", name="uq_team_vlr_id"),
        Index("ix_team_is_enc_2026", "is_enc_2026"),
    )


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = _pk()
    handle: Mapped[str] = mapped_column(Text, nullable=False)
    vlr_player_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("vlr_player_id", name="uq_player_vlr_id"),)


class TeamPlayer(Base):
    __tablename__ = "team_player"

    id: Mapped[int] = _pk()
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="CASCADE"), nullable=False)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("player.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("team_id", "player_id", name="uq_team_player"),
        Index("ix_team_player_player_id", "player_id"),
    )


class Map(Base):
    __tablename__ = "map"

    id: Mapped[int] = _pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    in_pool: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("name", name="uq_map_name"),)


class Match(Base):
    __tablename__ = "match"

    id: Mapped[int] = _pk()
    vlr_match_id: Mapped[str] = mapped_column(Text, nullable=False)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # Match identity + outcome (Phase 2; nullable — backfilled offline from cached HTML).
    team_a_id: Mapped[int | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), nullable=True
    )
    team_b_id: Mapped[int | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), nullable=True
    )
    winner_team_id: Mapped[int | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), nullable=True
    )
    score_a: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_b: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("vlr_match_id", name="uq_match_vlr_id"),
        Index("ix_match_played_at", "played_at"),
        Index("ix_match_event", "event"),
        Index("ix_match_team_a_id", "team_a_id"),
        Index("ix_match_team_b_id", "team_b_id"),
        Index("ix_match_winner_team_id", "winner_team_id"),
    )


class MatchMap(Base):
    __tablename__ = "match_map"

    id: Mapped[int] = _pk()
    match_id: Mapped[int] = mapped_column(
        ForeignKey("match.id", ondelete="CASCADE"), nullable=False
    )
    map_id: Mapped[int] = mapped_column(ForeignKey("map.id", ondelete="RESTRICT"), nullable=False)
    winner_team_id: Mapped[int | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        UniqueConstraint("match_id", "map_id", name="uq_match_map"),
        Index("ix_match_map_map_id", "map_id"),
        Index("ix_match_map_match_id", "match_id"),
    )


class PlayerMapStat(Base):
    __tablename__ = "player_map_stat"

    id: Mapped[int] = _pk()
    match_map_id: Mapped[int] = mapped_column(
        ForeignKey("match_map.id", ondelete="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        ForeignKey("player.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int | None] = mapped_column(
        ForeignKey("team.id", ondelete="SET NULL"), nullable=True
    )
    rating: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    acs: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    kast: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    adr: Mapped[float | None] = mapped_column(Numeric(6, 1), nullable=True)
    kills: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deaths: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assists: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("match_map_id", "player_id", name="uq_player_map_stat"),
        Index("ix_player_map_stat_player_id", "player_id"),
        Index("ix_player_map_stat_team_id", "team_id"),
        Index("ix_player_map_stat_match_map_id", "match_map_id"),
    )


# --------------------------------------------------------------------------- #
# Derived / output entities (lineage = inputs + config; no external provenance) #
# --------------------------------------------------------------------------- #
class Ranking(Base):
    __tablename__ = "ranking"

    id: Mapped[int] = _pk()
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tournament_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    data_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    data_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    config_hash: Mapped[str] = mapped_column(Text, nullable=False)
    supersedes_ranking_id: Mapped[int | None] = mapped_column(
        ForeignKey("ranking.id", ondelete="RESTRICT"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    entries: Mapped[list[RankingEntry]] = relationship(
        back_populates="ranking", cascade="all, delete-orphan"
    )
    map_breakdowns: Mapped[list[RankingMapBreakdown]] = relationship(
        back_populates="ranking", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("version", name="uq_ranking_version"),)


class RankingEntry(Base):
    __tablename__ = "ranking_entry"

    id: Mapped[int] = _pk()
    ranking_id: Mapped[int] = mapped_column(
        ForeignKey("ranking.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="RESTRICT"), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    team_score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    confidence: Mapped[str] = mapped_column(Text, nullable=False)

    ranking: Mapped[Ranking] = relationship(back_populates="entries")

    __table_args__ = (
        UniqueConstraint("ranking_id", "team_id", name="uq_ranking_entry_team"),
        UniqueConstraint("ranking_id", "position", name="uq_ranking_entry_position"),
        CheckConstraint("position BETWEEN 1 AND 16", name="ck_ranking_entry_position"),
    )


class RankingMapBreakdown(Base):
    __tablename__ = "ranking_map_breakdown"

    id: Mapped[int] = _pk()
    ranking_id: Mapped[int] = mapped_column(
        ForeignKey("ranking.id", ondelete="CASCADE"), nullable=False
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("team.id", ondelete="RESTRICT"), nullable=False)
    map_id: Mapped[int] = mapped_column(ForeignKey("map.id", ondelete="RESTRICT"), nullable=False)
    map_score: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    confidence: Mapped[str] = mapped_column(Text, nullable=False)

    ranking: Mapped[Ranking] = relationship(back_populates="map_breakdowns")

    __table_args__ = (
        UniqueConstraint("ranking_id", "team_id", "map_id", name="uq_ranking_map_breakdown"),
    )


class OutcomeComparison(Base):
    __tablename__ = "outcome_comparison"

    id: Mapped[int] = _pk()
    ranking_id: Mapped[int] = mapped_column(
        ForeignKey("ranking.id", ondelete="CASCADE"), nullable=False
    )
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metric: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    baseline_label: Mapped[str] = mapped_column(Text, nullable=False)
    baseline_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    final_standings_source: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("ranking_id", "metric", "baseline_label", name="uq_outcome_comparison"),
    )
