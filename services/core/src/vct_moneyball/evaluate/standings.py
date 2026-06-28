"""Final-standings loader/validator for post-tournament evaluation.

The standings file is JSON:

    {
      "source": "https://www.vlr.gg/event/...",      # provenance (required)
      "final": ["TeamA", "TeamB", ...],               # actual order, best first
      "baselines": {"vlr-seed": ["TeamB", "TeamA", ...]}  # optional baseline orders
    }

Validation: ``final`` is a non-empty list of unique team names; each baseline (if
present) ranks the same set. Raises :class:`CliError` on any malformation (FR-011).
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field

from vct_moneyball.common.logging import CliError


@dataclass(frozen=True)
class Standings:
    source: str
    final: list[str]
    baselines: dict[str, list[str]] = field(default_factory=dict)

    def baseline(self, label: str) -> list[str]:
        if label not in self.baselines:
            raise CliError(
                f"baseline {label!r} not present in standings; available: "
                f"{sorted(self.baselines) or 'none'}"
            )
        return self.baselines[label]


def _check_order(order: object, what: str) -> list[str]:
    if not isinstance(order, list) or not order:
        raise CliError(f"{what} must be a non-empty list of team names")
    if not all(isinstance(t, str) and t for t in order):
        raise CliError(f"{what} must contain only non-empty team-name strings")
    if len(order) != len(set(order)):
        raise CliError(f"{what} contains duplicate team names")
    return list(order)


def load_standings(path: str | pathlib.Path) -> Standings:
    p = pathlib.Path(path)
    if not p.is_file():
        raise CliError(f"standings file not found: {p}")
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as exc:
        raise CliError(f"standings file is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise CliError("standings file must be a JSON object")

    source = data.get("source")
    if not isinstance(source, str) or not source:
        raise CliError("standings file must record a non-empty 'source'")

    final = _check_order(data.get("final"), "'final'")
    final_set = set(final)

    baselines: dict[str, list[str]] = {}
    raw_baselines = data.get("baselines", {})
    if raw_baselines and not isinstance(raw_baselines, dict):
        raise CliError("'baselines' must be an object of label -> ordering")
    for label, order in (raw_baselines or {}).items():
        checked = _check_order(order, f"baseline {label!r}")
        if set(checked) != final_set:
            raise CliError(f"baseline {label!r} must rank the same teams as 'final'")
        baselines[label] = checked

    return Standings(source=source, final=final, baselines=baselines)
