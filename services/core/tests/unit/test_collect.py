"""Unit tests for the collect layer: roster parsing, cache, and cache-first fetcher."""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest

from vct_moneyball.collect.cache import RawHtmlCache
from vct_moneyball.collect.client import Fetcher
from vct_moneyball.collect.targets import (
    parse_match_urls,
    parse_player_matches,
    parse_team_roster,
    player_matches_url,
)

pytestmark = pytest.mark.unit

TEAM_FIXTURE = pathlib.Path(__file__).parent.parent / "fixtures" / "vlr" / "team_sample.html"
TEAM_URL = "https://www.vlr.gg/team/1184/fut-esports"


def test_parse_team_roster_real_fixture() -> None:
    roster = parse_team_roster(TEAM_FIXTURE.read_text(), team_url=TEAM_URL)
    assert roster.name == "FUT Esports"
    assert roster.country == "Türkiye"
    assert roster.vlr_team_id == "1184"
    handles = {m.handle for m in roster.members}
    assert {"s0pp", "xeus", "yetujey"} <= handles
    # Active players are flagged; inactive ones carry is_active=False.
    active = [m for m in roster.members if m.is_active]
    assert len(active) >= 5
    assert any(not m.is_active for m in roster.members)  # baha/AtaKaptan are inactive


def test_parse_match_urls_dedupes_trailing_slash() -> None:
    # VLR links the same match with and without a trailing slash (and with a query);
    # they must collapse to a single normalized URL (respectful: no duplicate fetch).
    html = """
    <a href="/670474/team-vitality-vs-fut-esports-masters-london">a</a>
    <a href="/670474/team-vitality-vs-fut-esports-masters-london/">b</a>
    <a href="/670474/team-vitality-vs-fut-esports-masters-london/?map=2">c</a>
    <a href="/team/1184/fut-esports">not-a-match</a>
    """
    urls = parse_match_urls(html)
    assert urls == ["https://www.vlr.gg/670474/team-vitality-vs-fut-esports-masters-london"]


PLAYER_MATCHES_HTML = """
<html><body>
  <a class="wf-card m-item" href="/706327/qor-vs-yft-r6">
     <div class="m-item-date">2026/06/27 8:20 pm</div></a>
  <a class="wf-card m-item" href="/701227/qor-vs-evictix-r5/">
     <div class="m-item-date">2026/06/24 5:00 pm</div></a>
  <a class="wf-card m-item" href="/100000/old-match">
     <div class="m-item-date">2024/01/01 1:00 pm</div></a>
  <a class="wf-card" href="/team/6985/qor">not a match</a>
</body></html>
"""


def test_player_matches_url() -> None:
    assert (
        player_matches_url("https://www.vlr.gg/player/25745/kumi")
        == "https://www.vlr.gg/player/matches/25745/kumi/"
    )


def test_parse_player_matches_reads_dates_and_dedupes() -> None:
    refs = parse_player_matches(PLAYER_MATCHES_HTML)
    urls = [r.match_url for r in refs]
    assert "https://www.vlr.gg/706327/qor-vs-yft-r6" in urls
    assert "https://www.vlr.gg/team/6985/qor" not in urls  # not a match link
    by_url = {r.match_url: r.played_at for r in refs}
    assert by_url["https://www.vlr.gg/706327/qor-vs-yft-r6"] == datetime(
        2026, 6, 27, 20, 20, tzinfo=UTC
    )


def test_cache_roundtrip_and_latest(tmp_path: pathlib.Path) -> None:
    cache = RawHtmlCache(tmp_path)
    url = "https://example.test/page"
    assert not cache.has(url)
    cache.write(url, "<html>1</html>", datetime(2026, 1, 1, tzinfo=UTC))
    cache.write(url, "<html>2</html>", datetime(2026, 1, 2, tzinfo=UTC))
    assert cache.has(url)
    latest = cache.read_latest(url)
    assert latest is not None
    assert latest.html == "<html>2</html>"  # most recent capture
    assert latest.captured_at == datetime(2026, 1, 2, tzinfo=UTC)


def test_fetcher_prefers_cache(tmp_path: pathlib.Path) -> None:
    cache = RawHtmlCache(tmp_path)
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        return "<live/>"

    fetcher = Fetcher(cache, use_cache=True, fetch_fn=fake_fetch, clock=lambda: datetime.now(UTC))
    url = "https://example.test/x"
    first = fetcher.fetch(url)  # cache miss -> live
    second = fetcher.fetch(url)  # cache hit -> no second live call
    assert first.html == "<live/>"
    assert second.html == "<live/>"
    assert calls == [url]  # fetched exactly once


def test_fetcher_errors_when_unreachable_and_no_cache(tmp_path: pathlib.Path) -> None:
    cache = RawHtmlCache(tmp_path)

    def boom(url: str) -> str:
        raise RuntimeError("network down")

    fetcher = Fetcher(cache, use_cache=True, fetch_fn=boom)
    with pytest.raises(Exception):  # noqa: B017
        fetcher.fetch("https://example.test/y")
