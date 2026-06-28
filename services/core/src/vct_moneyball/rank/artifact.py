"""Ranking artifact: build the JSON (schema-validated) + Markdown, write immutably.

The published artifact is the locked record (Constitution II). This module turns the
aggregated ranking into the ``ranking.json`` shape defined by
``contracts/ranking-artifact.schema.json``, validates it, renders a human-readable
``ranking.md``, and writes both into a per-publish directory that is **never**
overwritten (append-only; ``--supersedes`` links a correction to the original).
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime
from functools import lru_cache
from typing import Any

import jsonschema

from vct_moneyball.common.logging import CliError
from vct_moneyball.rank.aggregate import TeamRanking

_SCHEMA_REL = pathlib.PurePath(
    "specs", "001-enc-power-ranking", "contracts", "ranking-artifact.schema.json"
)


def _find_repo_root() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / _SCHEMA_REL).is_file():
            return base
    raise CliError(f"could not locate {_SCHEMA_REL} from cwd or module path")


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    path = _find_repo_root() / _SCHEMA_REL
    return json.loads(path.read_text())


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _round(value: float) -> float:
    return round(float(value), 4)


def build_artifact(
    ranking: list[TeamRanking],
    *,
    version: str,
    published_at: datetime,
    tournament_start: datetime,
    data_window: tuple[datetime, datetime],
    config_hash: str,
    map_pool: list[str],
    supersedes: str | None = None,
) -> dict[str, Any]:
    """Assemble the artifact dict (does not validate; call :func:`validate_artifact`)."""
    return {
        "version": version,
        "published_at": _iso(published_at),
        "tournament_start": _iso(tournament_start),
        "supersedes": supersedes,
        "data_window": {"start": _iso(data_window[0]), "end": _iso(data_window[1])},
        "config_hash": config_hash,
        "map_pool": list(map_pool),
        "teams": [
            {
                "position": t.position,
                "team": t.team,
                "country": t.country,
                "team_score": _round(t.team_score),
                "confidence": t.confidence,
                "map_breakdown": [
                    {
                        "map": b.map,
                        "map_score": _round(b.map_score),
                        "confidence": b.confidence,
                    }
                    for b in t.map_breakdown
                ],
                "contributors": [
                    {
                        "player": c.player,
                        "player_score": _round(c.player_score),
                        "confidence": c.confidence,
                        "maps_played": c.maps_played,
                        "low_history_baseline": c.low_history_baseline,
                    }
                    for c in t.contributors
                ],
            }
            for t in ranking
        ],
    }


def validate_artifact(artifact: dict[str, Any]) -> None:
    """Validate against the JSON Schema contract; raise :class:`CliError` on failure."""
    try:
        jsonschema.validate(artifact, _schema())
    except jsonschema.ValidationError as exc:
        raise CliError(f"ranking artifact failed schema validation: {exc.message}") from exc


def render_markdown(artifact: dict[str, Any]) -> str:
    """Render the human-readable ranking table."""
    lines = [
        f"# ENC 2026 Power Ranking — `{artifact['version']}`",
        "",
        f"- Published: `{artifact['published_at']}`",
        f"- Tournament start (lock deadline): `{artifact['tournament_start']}`",
        f"- Data window: `{artifact['data_window']['start']}` → `{artifact['data_window']['end']}`",
        f"- Config hash: `{artifact['config_hash']}`",
    ]
    if artifact.get("supersedes"):
        lines.append(f"- Supersedes: `{artifact['supersedes']}`")
    lines += [
        "",
        "| # | Team | Country | Score | Confidence |",
        "|--:|------|---------|------:|------------|",
    ]
    for t in artifact["teams"]:
        lines.append(
            f"| {t['position']} | {t['team']} | {t['country']} | "
            f"{t['team_score']:.4f} | {t['confidence']} |"
        )
    lines.append("")
    return "\n".join(lines)


def write_artifact(
    artifact: dict[str, Any], out_dir: pathlib.Path, *, slug: str | None = None
) -> pathlib.Path:
    """Write ``ranking.json`` + ``ranking.md`` into a fresh per-publish directory.

    Refuses to overwrite an existing directory (immutability — Constitution II).
    """
    slug = slug or artifact["published_at"].replace(":", "").replace("+", "Z")
    target = out_dir / slug
    if target.exists():
        raise CliError(f"refusing to overwrite existing artifact directory: {target}")
    target.mkdir(parents=True)
    (target / "ranking.json").write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    (target / "ranking.md").write_text(render_markdown(artifact))
    return target
