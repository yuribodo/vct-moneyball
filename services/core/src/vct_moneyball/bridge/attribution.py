"""Player-side attribution: which side of a match each player was on.

Derived from the parsed match's stats tables (first overview table = team_a, second =
team_b), keyed by the player's VLR id. Offline and exact (no fuzzy name matching), so a
player's club results can be attributed to win/loss for the player-Elo replay (R1).
"""

from __future__ import annotations

from vct_moneyball.collect.parse import ParsedMatch


def sides_for_match(parsed: ParsedMatch) -> dict[str, int]:
    """Map ``vlr_player_id`` -> side index (0 = team_a, 1 = team_b).

    A player is on one side for the whole match; the first occurrence wins. Players with no
    VLR id are omitted (cannot be attributed reliably).
    """
    sides: dict[str, int] = {}
    for parsed_map in parsed.maps:
        for stat in parsed_map.players:
            if stat.vlr_player_id and stat.vlr_player_id not in sides:
                sides[stat.vlr_player_id] = stat.team_index
    return sides


def side_team_id(side_index: int, team_a_id: int, team_b_id: int) -> int:
    return team_a_id if side_index == 0 else team_b_id
