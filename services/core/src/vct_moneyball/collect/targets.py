"""ENC cohort discovery: teams, rosters, and in-window matches.

The exact ENC 2026 teams/rosters and the event are *runtime data* (research "Open
items"), not hardcoded. The cohort source is supplied via config/env
(``VCTM_ENC_TEAMS`` — VLR team URLs — or ``VCTM_ENC_EVENT_URL``). Parsing of team and
match-list pages is pure and offline-testable; orchestration uses the cache-first
:class:`~vct_moneyball.collect.client.Fetcher`.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime

from bs4 import BeautifulSoup

from vct_moneyball.collect.client import Fetcher
from vct_moneyball.common.logging import CliError

VLR_BASE = "https://www.vlr.gg"


@dataclass(frozen=True)
class RosterMember:
    handle: str
    vlr_player_id: str | None
    player_url: str | None
    role: str | None
    is_active: bool


@dataclass
class TeamRoster:
    name: str
    country: str
    vlr_team_id: str | None
    team_url: str
    members: list[RosterMember] = field(default_factory=list)


def _normalize(url: str) -> str:
    """Drop the query string and any trailing slash so equivalent URLs dedup."""
    base = url.split("?")[0].split("#")[0].rstrip("/")
    return base if base.startswith("http") else f"{VLR_BASE}{base}"


def _abs(url: str) -> str:
    return _normalize(url)


def _team_id_from_url(url: str) -> str | None:
    m = re.search(r"/team/(\d+)/", url)
    return m.group(1) if m else None


def parse_team_roster(html: str, *, team_url: str) -> TeamRoster:
    """Parse a VLR.gg team page into a roster (active players + status)."""
    soup = BeautifulSoup(html, "html.parser")

    name_el = soup.select_one(".team-header-name .wf-title, .team-header-name h1, .wf-title")
    name = name_el.get_text(strip=True) if name_el else ""
    country_el = soup.select_one(".team-header-country")
    country = country_el.get_text(strip=True) if country_el else ""

    members: list[RosterMember] = []
    for item in soup.select(".team-roster-item"):
        link = item.select_one("a[href^='/player/']")
        if link is None:
            continue
        href = str(link.get("href", ""))
        pid_m = re.search(r"/player/(\d+)/", href)
        alias_el = item.select_one(".team-roster-item-name-alias")
        handle = alias_el.get_text(strip=True) if alias_el else link.get_text(strip=True)
        tags = " ".join(t.get_text(strip=True).lower() for t in item.select(".wf-tag"))
        is_staff = "staff" in tags or "coach" in tags or "manager" in tags
        is_inactive = "inactive" in tags
        role = None
        for t in item.select(".wf-tag"):
            txt = t.get_text(strip=True)
            if txt and txt.lower() not in {"inactive"}:
                role = txt
                break
        if is_staff:
            continue
        members.append(
            RosterMember(
                handle=handle,
                vlr_player_id=pid_m.group(1) if pid_m else None,
                player_url=_abs(href),
                role=role,
                is_active=not is_inactive,
            )
        )
    return TeamRoster(
        name=name,
        country=country,
        vlr_team_id=_team_id_from_url(team_url),
        team_url=_abs(team_url),
        members=members,
    )


def parse_event_team_urls(html: str) -> list[str]:
    """Extract participating team URLs from a VLR.gg event page."""
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for link in soup.select("a[href^='/team/']"):
        href = str(link.get("href", ""))
        if re.search(r"/team/\d+/", href):
            abs_url = _normalize(href)
            if abs_url not in urls:
                urls.append(abs_url)
    return urls


def parse_match_urls(html: str, *, in_window: datetime | None = None) -> list[str]:
    """Extract unique match page URLs from a VLR.gg match-list/results page."""
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for link in soup.select("a[href]"):
        href = str(link.get("href", ""))
        if re.match(r"^/\d{4,8}/[a-z0-9-]+", href):
            abs_url = _normalize(href)
            if abs_url not in urls:
                urls.append(abs_url)
    return urls


def resolve_cohort_team_urls(fetcher: Fetcher) -> list[str]:
    """Resolve the 16 ENC team URLs from config/env (runtime data, not hardcoded)."""
    explicit = os.environ.get("VCTM_ENC_TEAMS", "").strip()
    if explicit:
        return [_abs(u.strip()) for u in explicit.split(",") if u.strip()]

    event_url = os.environ.get("VCTM_ENC_EVENT_URL", "").strip()
    if event_url:
        page = fetcher.fetch(_abs(event_url))
        return parse_event_team_urls(page.html)

    raise CliError(
        "no ENC cohort source configured: set VCTM_ENC_TEAMS (comma-separated VLR team "
        "URLs) or VCTM_ENC_EVENT_URL (the ENC event page)"
    )


def discover_rosters(fetcher: Fetcher, team_urls: list[str]) -> list[TeamRoster]:
    """Fetch + parse each team page into a roster."""
    rosters: list[TeamRoster] = []
    for url in team_urls:
        page = fetcher.fetch(url)
        rosters.append(parse_team_roster(page.html, team_url=url))
    return rosters
