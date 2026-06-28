"""Event-tier classification — a transparent strength-of-schedule proxy.

The MVP composite (R1) ignores who a player faced, so stat-padding against weak
opposition counts the same as suppressed output in tier-1 play. As a transparent,
deterministic correction we weight each performance by the *tier* of the event it
came from (the weights live in versioned config). This is keyword-based and explainable
— not a learned opponent model (that is Phase 2).

Tiers (by VLR event naming, 2026 season):
- ``t1`` — international / franchised league play (Champions, Masters, VCT
  Americas/EMEA/Pacific/China, Esports World Cup).
- ``t2`` — regional development circuits (Challengers, Ascension, Game Changers, VCL).
- ``t3`` — everything else (national-team events, qualifiers, minor/local).
"""

from __future__ import annotations

_T1_KEYWORDS = ("champions", "masters", "esports world cup", "ewc", "radiant")
_T1_VCT_REGIONS = ("americas", "emea", "pacific", "china")
_T2_KEYWORDS = ("challengers", "ascension", "game changers", "vcl", "rising")


def classify_event_tier(event: str | None) -> str:
    """Classify an event name into ``t1`` | ``t2`` | ``t3``."""
    e = (event or "").lower()
    if any(k in e for k in _T1_KEYWORDS):
        return "t1"
    if "vct" in e and any(r in e for r in _T1_VCT_REGIONS):
        return "t1"
    if any(k in e for k in _T2_KEYWORDS):
        return "t2"
    return "t3"
