"""T016 — VLR parser turns fixture HTML into stat records with provenance."""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest

from vct_moneyball.collect.parse import parse_match

pytestmark = pytest.mark.unit

FIXTURE = pathlib.Path(__file__).parent.parent / "fixtures" / "vlr" / "match_706327.html"
SOURCE_URL = (
    "https://www.vlr.gg/706327/qor-vs-yft-challengers-2026-north-america-ace-stage-3-r6-3-2"
)
CAPTURED_AT = datetime(2026, 6, 27, 20, 0, tzinfo=UTC)


@pytest.fixture
def html() -> str:
    return FIXTURE.read_text()


def test_parses_match_identity(html: str) -> None:
    match = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    assert match.vlr_match_id == "706327"
    assert "Challengers 2026" in match.event
    assert set(match.team_abbrevs) >= {"QOR", "YFT"}


def test_parses_all_maps_with_full_rosters(html: str) -> None:
    match = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    assert [m.map_name for m in match.maps] == ["Lotus", "Haven", "Breeze"]
    for parsed_map in match.maps:
        assert len(parsed_map.players) == 10  # 5v5


def test_every_stat_carries_provenance(html: str) -> None:
    match = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    for parsed_map in match.maps:
        for stat in parsed_map.players:
            assert stat.source_url == SOURCE_URL
            assert stat.captured_at == CAPTURED_AT


def test_parses_known_player_values(html: str) -> None:
    match = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    lotus = match.maps[0]
    kumi = next(p for p in lotus.players if p.handle == "kumi")
    assert kumi.vlr_player_id == "25745"
    assert kumi.rating == pytest.approx(1.61)
    assert kumi.acs == pytest.approx(304.0)
    assert kumi.kast == pytest.approx(80.0)
    assert kumi.adr == pytest.approx(189.0)
    assert (kumi.kills, kumi.deaths, kumi.assists) == (24, 9, 0)


def test_parse_is_deterministic(html: str) -> None:
    a = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    b = parse_match(html, source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    assert a == b
