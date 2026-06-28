"""Unit tests for the collect layer: roster parsing, cache, and cache-first fetcher."""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest

from vct_moneyball.collect.cache import RawHtmlCache
from vct_moneyball.collect.client import Fetcher
from vct_moneyball.collect.targets import parse_team_roster

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
