"""Pure parsers: VLR.gg HTML -> structured records.

Parsing is a pure function of cached HTML (R5), so it is deterministic and unit-
testable offline against committed fixtures. Every record carries provenance
(``source_url`` + ``captured_at``) threaded in by the caller (Constitution I).

The VLR match-page DOM (as of the 2026 season):

- ``div.vm-stats-gamesnav-item.js-map-switch[data-game-id]`` — map switcher; text is
  ``"<order> <MapName>"`` (e.g. ``"1 Lotus"``); ``data-game-id="all"`` is the summary.
- ``div.vm-stats-game[data-game-id]`` — one per played map; contains two
  ``table.wf-table-inset.mod-overview`` (one per team).
- A player row: ``td.mod-player`` (handle in ``.text-of``, ``a[href="/player/<id>/..."]``,
  team abbreviation in ``.ge-text-light``), followed by ``td.mod-stat`` cells in column
  order: Rating, ACS, K, D, A, +/-, KAST, ADR, HS%, FK, FD, +/-. Each stat cell exposes
  ``.mod-both`` (both-sides value), which we read.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

from bs4 import BeautifulSoup, Tag

# mod-stat column order on the overview table.
_STAT_COLUMNS = ("rating", "acs", "kills", "deaths", "assists", "pm", "kast", "adr")


@dataclass
class ParsedPlayerStat:
    handle: str
    vlr_player_id: str | None
    team_abbrev: str
    rating: float | None
    acs: float | None
    kast: float | None
    adr: float | None
    kills: int | None
    deaths: int | None
    assists: int | None
    source_url: str
    captured_at: datetime


@dataclass
class ParsedMap:
    map_name: str
    vlr_game_id: str
    players: list[ParsedPlayerStat] = field(default_factory=list)


@dataclass
class ParsedMatch:
    vlr_match_id: str
    event: str
    played_at: datetime | None
    team_abbrevs: list[str]
    maps: list[ParsedMap]
    source_url: str
    captured_at: datetime


def _num(text: str | None) -> float | None:
    """Parse a VLR stat cell like ``'304'``, ``'1.61'``, ``'80%'`` into a number."""
    if text is None:
        return None
    cleaned = text.strip().replace("%", "").replace("+", "")
    if cleaned in {"", "-", "/"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _int(text: str | None) -> int | None:
    val = _num(text)
    return int(val) if val is not None else None


def _match_id_from_url(source_url: str) -> str:
    m = re.search(r"/(\d{4,8})(?:/|$)", source_url)
    return m.group(1) if m else source_url.rstrip("/").rsplit("/", 1)[-1]


def _map_names(soup: BeautifulSoup) -> dict[str, str]:
    """Map ``data-game-id`` -> map name from the games navigation."""
    names: dict[str, str] = {}
    for item in soup.select(".vm-stats-gamesnav-item.js-map-switch"):
        gid = item.get("data-game-id")
        if not gid or gid == "all":
            continue
        text = re.sub(r"\s+", " ", item.get_text(" ", strip=True))
        # Strip a leading order number ("1 Lotus" -> "Lotus").
        name = re.sub(r"^\d+\s+", "", text).strip()
        if isinstance(gid, str) and name:
            names[gid] = name
    return names


def _map_name_from_header(game: Tag) -> str | None:
    """Read a map name from a game's own header — used for Bo1s with no map nav."""
    map_el = game.select_one(".vm-stats-game-header .map")
    if map_el is None:
        return None
    # Header text looks like "Lotus -"; take the first alphabetic run.
    m = re.search(r"[A-Za-z]+", map_el.get_text(" ", strip=True))
    return m.group(0) if m else None


def _parse_player_row(
    row: Tag, *, source_url: str, captured_at: datetime
) -> ParsedPlayerStat | None:
    name_el = row.select_one(".mod-player .text-of")
    if name_el is None:
        return None
    handle = name_el.get_text(strip=True)

    vlr_player_id: str | None = None
    link = row.select_one(".mod-player a[href]")
    if link is not None:
        href = str(link.get("href", ""))
        m = re.search(r"/player/(\d+)/", href)
        if m:
            vlr_player_id = m.group(1)

    abbrev_el = row.select_one(".mod-player .ge-text-light")
    team_abbrev = abbrev_el.get_text(strip=True) if abbrev_el else ""

    values: dict[str, str | None] = {}
    for i, cell in enumerate(row.select("td.mod-stat")):
        if i >= len(_STAT_COLUMNS):
            break
        both = cell.select_one(".mod-both")
        values[_STAT_COLUMNS[i]] = both.get_text(strip=True) if both else None

    return ParsedPlayerStat(
        handle=handle,
        vlr_player_id=vlr_player_id,
        team_abbrev=team_abbrev,
        rating=_num(values.get("rating")),
        acs=_num(values.get("acs")),
        kast=_num(values.get("kast")),
        adr=_num(values.get("adr")),
        kills=_int(values.get("kills")),
        deaths=_int(values.get("deaths")),
        assists=_int(values.get("assists")),
        source_url=source_url,
        captured_at=captured_at,
    )


def parse_match(html: str, *, source_url: str, captured_at: datetime) -> ParsedMatch:
    """Parse a VLR.gg match page into a :class:`ParsedMatch`."""
    soup = BeautifulSoup(html, "html.parser")

    event_el = soup.select_one(".match-header-event div[style*='font-weight: 700']")
    event = event_el.get_text(" ", strip=True) if event_el else ""

    played_at: datetime | None = None
    ts_el = soup.select_one("[data-utc-ts]")
    if ts_el is not None:
        raw = str(ts_el.get("data-utc-ts", "")).strip()
        try:
            parsed_ts = datetime.fromisoformat(raw)
            # VLR's data-utc-ts is UTC but carries no offset; make it tz-aware.
            played_at = parsed_ts if parsed_ts.tzinfo else parsed_ts.replace(tzinfo=UTC)
        except ValueError:
            played_at = None

    map_names = _map_names(soup)

    maps: list[ParsedMap] = []
    abbrevs: list[str] = []
    for game in soup.select(".vm-stats-game"):
        gid = game.get("data-game-id")
        if not isinstance(gid, str) or gid == "all":
            continue
        map_name = map_names.get(gid) or _map_name_from_header(game) or f"game-{gid}"
        parsed_map = ParsedMap(map_name=map_name, vlr_game_id=gid)
        for table in game.select("table.wf-table-inset.mod-overview"):
            for row in table.select("tbody tr"):
                stat = _parse_player_row(row, source_url=source_url, captured_at=captured_at)
                if stat is not None:
                    parsed_map.players.append(stat)
                    if stat.team_abbrev and stat.team_abbrev not in abbrevs:
                        abbrevs.append(stat.team_abbrev)
        if parsed_map.players:
            maps.append(parsed_map)

    return ParsedMatch(
        vlr_match_id=_match_id_from_url(source_url),
        event=event,
        played_at=played_at,
        team_abbrevs=abbrevs,
        maps=maps,
        source_url=source_url,
        captured_at=captured_at,
    )
