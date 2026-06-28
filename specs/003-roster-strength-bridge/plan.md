# Implementation Plan: ENC Roster-Strength Bridge (Phase 3)

**Branch**: `003-roster-strength-bridge` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-roster-strength-bridge/spec.md`

## Summary

Turn the honest ~50/50 abstention on ENC national-team matchups into confident, calibrated
predictions by deriving each team's strength from its **active roster's club performance**.
The signal is a chronologically-updated **player Elo** (each player's rating moves with the
results of the club matches they played), aggregated over a roster into a team strength; a
small calibrated model maps the roster-strength difference to a win probability. It is
trained and **honestly evaluated on real club matches with known lineups** (where outcomes
exist), then applied to the 16 ENC rosters — always leakage-free, baseline-relative, and
traceable (Constitution IV). The one prerequisite: attribute each player to the **side** they
played on in each match (populate the existing, currently-null `player_map_stat.team_id`),
re-derived offline from the cached HTML.

## Technical Context

**Language/Version**: Python 3.12 (uv, `services/core/`).

**Primary Dependencies**: reuse feature-002 stack — scikit-learn (calibrated logistic
regression), pandas/numpy, MLflow (tracking), SQLAlchemy 2.0. No new third-party deps.

**Storage**: PostgreSQL 16 (feature-001/002 schema). **No new columns** — the bridge
populates the existing `player_map_stat.team_id` (player's side per match) via an offline
re-parse, and reads rosters/players/matches/outcomes. Reports are committed artifacts under
`artifacts/models/bridge/`; runs tracked in MLflow (`mlruns/`).

**Testing**: pytest (unit + integration on fixtures). Leakage tests assert player Elo and
roster strength as-of a date use only prior matches; evaluation runs on a verified held-out
split of real club matches.

**Target Platform**: Linux (local dev + Docker). Batch CLI.

**Project Type**: Single Python project under `services/core/` (extends 001/002).

**Performance Goals**: Not latency-sensitive; player-Elo replay over ~1k matches + roster
aggregation completes offline in seconds.

**Constraints**: Strict temporal correctness (player strength uses only pre-as-of matches —
verified); reproducible from versioned inputs + config; every strength traceable to its
contributing players + run; honest baseline-relative reporting; sparse rosters flagged, never
guessed.

**Scale/Scope**: 16 ENC teams, ~108 rostered players, ~1.1k labeled club matches, a handful
of roster-derived features.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Reproducible Data Provenance | Player-side attribution is re-derived offline from cached HTML (no hand-editing); strengths are pure functions of versioned inputs + config; runs fingerprinted. | ✅ |
| II. Falsifiable, Locked Predictions | Roster-derived ENC ranking/forecast is published as a dated, immutable artifact citing its run; never overwrites 001/002 artifacts. | ✅ |
| III. Test-First & E2E Validation | TDD; leakage + as-of correctness tested on fixtures; one real matchup validated end-to-end before scaling. | ✅ |
| IV. Honest Model Evaluation | Leakage-free temporal split on real club matches; explicit baseline (roster-tier pedigree / naive player-rating average) on identical matches; MLflow-tracked; non-improvement reported. | ✅ Core of the feature. |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/003-roster-strength-bridge/
├── plan.md          # This file
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
├── contracts/       # Phase 1 output (CLI + report schema)
└── tasks.md         # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
services/core/
├── src/vct_moneyball/
│   ├── collect/parse.py            # (already) per-player team_abbrev — used for attribution
│   ├── cli/
│   │   ├── backfill_sides.py       # vctm backfill-sides (populate player_map_stat.team_id)
│   │   ├── enc_predict.py          # vctm enc-predict  (confident ENC matchup)
│   │   ├── enc_ranking.py          # vctm enc-ranking  (roster-derived 16-team ranking)
│   │   └── eval_bridge.py          # vctm eval-bridge  (honest eval vs baseline)
│   └── bridge/                     # NEW — the roster-strength bridge
│       ├── attribution.py          # map each player_map_stat to the match side (team_id)
│       ├── player_rating.py        # leakage-free chronological player Elo + form
│       ├── strength.py             # roster/lineup → team strength as-of (+ confidence)
│       ├── features.py             # roster-derived matchup features (diff encoding)
│       ├── baselines.py            # pedigree + naive player-rating-average baselines
│       └── evaluate.py             # bridge vs baseline on held-out club matches
└── tests/{unit,integration,fixtures}

artifacts/
└── models/bridge/                  # committed bridge eval reports + ENC ranking (JSON+MD)
```

**Structure Decision**: Extend the single `services/core/` project with a new `bridge/`
package that composes the existing layers: it re-uses feature-002's calibrated model,
metrics, tracking, and report discipline, and feature-001's roster + pedigree. The only
data change is populating an existing column (`player_map_stat.team_id`) offline. New `vctm`
subcommands expose backfill, ENC prediction, ENC ranking, and the honest bridge evaluation.

## Complexity Tracking

> No constitution violations — nothing to justify.
