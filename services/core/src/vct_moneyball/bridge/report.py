"""Bridge evaluation report: build, schema-validate, render, write.

Same discipline as the feature-002 report, validated against
``contracts/bridge-report.schema.json`` (adds ``aggregation`` + ``attribution_coverage``).
"""

from __future__ import annotations

import json
import pathlib
from datetime import datetime
from functools import lru_cache
from typing import Any

import jsonschema

from vct_moneyball.common.logging import CliError
from vct_moneyball.predict.evaluate import Metrics

_SCHEMA_REL = pathlib.PurePath(
    "specs", "003-roster-strength-bridge", "contracts", "bridge-report.schema.json"
)


def _repo_root() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / _SCHEMA_REL).is_file():
            return base
    raise CliError(f"could not locate {_SCHEMA_REL}")


@lru_cache(maxsize=1)
def _schema() -> dict[str, Any]:
    return json.loads((_repo_root() / _SCHEMA_REL).read_text())


def build_report(
    *,
    run_id: str,
    created_at: datetime,
    cutoff: datetime,
    data_window: tuple[datetime, datetime],
    feature_fingerprint: str,
    training_config: dict[str, str],
    n_train: int,
    n_eval: int,
    attribution_coverage: float,
    underpowered: bool,
    model: Metrics,
    baselines: list[tuple[str, Metrics]],
) -> dict[str, Any]:
    """``training_config`` carries ``aggregation``, ``learner``, ``calibration_method``
    (grouped to keep the parameter count reasonable — see python:S107)."""
    return {
        "run_id": run_id,
        "created_at": created_at.isoformat(),
        "cutoff": cutoff.isoformat(),
        "data_window": {"start": data_window[0].isoformat(), "end": data_window[1].isoformat()},
        "feature_fingerprint": feature_fingerprint,
        "aggregation": training_config["aggregation"],
        "learner": training_config["learner"],
        "calibration_method": training_config["calibration_method"],
        "n_train": n_train,
        "n_eval": n_eval,
        "attribution_coverage": round(attribution_coverage, 4),
        "underpowered": underpowered,
        "leakage_verified": True,
        "model": model.as_dict(),
        "baselines": [{"label": label, "metrics": m.as_dict()} for label, m in baselines],
    }


def validate_report(report: dict[str, Any]) -> None:
    try:
        jsonschema.validate(report, _schema())
    except jsonschema.ValidationError as exc:
        raise CliError(f"bridge report failed schema validation: {exc.message}") from exc


def render_markdown(report: dict[str, Any]) -> str:
    m = report["model"]
    lines = [
        "# Roster-Strength Bridge Evaluation",
        "",
        f"- Run: `{report['run_id']}`  ·  learner: `{report['learner']}`  ·  "
        f"aggregation: `{report['aggregation']}`  ·  calibration: `{report['calibration_method']}`",
        f"- Cutoff: `{report['cutoff']}`  ·  Train/Eval: {report['n_train']}/{report['n_eval']}"
        + ("  ⚠️ underpowered" if report.get("underpowered") else ""),
        f"- Attribution coverage: {report['attribution_coverage']:.1%}  ·  leakage verified: "
        f"{report['leakage_verified']}",
        "",
        "| Predictor | log-loss | accuracy | Brier | calib. err |",
        "|-----------|---------:|---------:|------:|-----------:|",
        f"| **bridge** | {m['log_loss']:.4f} | {m['accuracy']:.4f} | {m['brier']:.4f} | "
        f"{m['calibration_error']:.4f} |",
    ]
    for b in report["baselines"]:
        bm = b["metrics"]
        lines.append(
            f"| {b['label']} | {bm['log_loss']:.4f} | {bm['accuracy']:.4f} | {bm['brier']:.4f} | "
            f"{bm['calibration_error']:.4f} |"
        )
    best = min(report["baselines"], key=lambda b: b["metrics"]["log_loss"])
    verdict = "beats" if m["log_loss"] < best["metrics"]["log_loss"] else "does NOT beat"
    lines += [
        "",
        f"The roster-strength bridge **{verdict}** its best baseline "
        f"(`{best['label']}`) on log-loss.",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict[str, Any], out_dir: pathlib.Path) -> pathlib.Path:
    target = out_dir / report["run_id"]
    if target.exists():
        raise CliError(f"refusing to overwrite existing report dir: {target}")
    target.mkdir(parents=True)
    (target / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (target / "report.md").write_text(render_markdown(report))
    return target
