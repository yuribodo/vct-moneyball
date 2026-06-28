# Implementation Plan: Match Winrate Predictor (Phase 2)

**Branch**: `002-winrate-predictor` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-winrate-predictor/spec.md`

## Summary

Learn professional-Valorant match outcomes from the data feature 001 already collects,
and turn that into calibrated win probabilities for a matchup. The model is trained on
matches strictly **before** a cutoff and judged only on matches **on/after** it (no
leakage), always against an explicit baseline, with every run tracked (Constitution IV).
The MVP learner is a **regularized, probability-calibrated logistic regression over
opponent-difference features** — transparent and appropriate for ~1k matches — with
gradient-boosted trees as an optional, tracked alternative. A `vctm` CLI trains, predicts,
and produces a baseline-relative evaluation report. One prerequisite the spec implies: the
match **outcome label** (who won) must be reliably extracted — feature 001 captured player
stats but not the series result — so this plan adds offline winner extraction from the
already-cached HTML (no new scraping).

## Technical Context

**Language/Version**: Python 3.12 (uv, `services/core/`).

**Primary Dependencies**: scikit-learn (logistic regression + `CalibratedClassifierCV`),
pandas + numpy (feature building), MLflow (run/metric/param/artifact tracking), SQLAlchemy
2.0 (read feature-001 schema). XGBoost/LightGBM optional (already in the `ml` group) as a
tracked alternative learner. Reuses feature-001 `collect/parse` for the new winner field.

**Storage**: PostgreSQL 16 (feature-001 schema) is the data source. New: a match
**outcome** (winner + series score) persisted on the existing `match`/`match_map` rows via
an Alembic migration. MLflow uses a local file store (`mlruns/`, git-ignored, DVC-trackable
later). Evaluation reports are committed artifacts under `artifacts/models/winrate/`.

**Testing**: pytest (unit + integration on fixtures). Dedicated leakage tests assert the
temporal split has zero overlap and that no feature reads on/after the match date.

**Target Platform**: Linux (local dev + Docker). Batch CLI; no server runtime.

**Project Type**: Single Python project under `services/core/` (extends feature 001).

**Performance Goals**: Not latency-sensitive. Train + evaluate on the full collected set
(~1k–5k matches) completes offline in well under a minute; a single prediction is instant.

**Constraints**: Strict temporal correctness (no post-match info in any feature — verified,
not assumed); fully reproducible from versioned inputs + config; every reported number
traceable to its MLflow run; honest baseline-relative reporting.

**Scale/Scope**: ~1k–5k in-window professional matches, ~16 ENC teams + their opponents,
a small handful of engineered features per side.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Reproducible Data Provenance | Features derive only from provenance-bearing feature-001 rows; the new winner field is re-derived offline from cached HTML (no hand-editing); runs + datasets fingerprinted. | ✅ Winner extraction re-parses cached HTML; feature build is a pure function of versioned inputs + config. |
| II. Falsifiable, Locked Predictions | The model can serve as a forecast source; any *published* forecast remains a dated, immutable artifact citing the run that produced it. | ✅ Eval reports are append-only artifacts; the ENC forecast (if published) reuses the feature-001 locking discipline. |
| III. Test-First & E2E Validation | TDD with pytest; leakage + split correctness tested on fixtures; one real match validated end-to-end (label + features + prediction) before scaling. | ✅ Planned: leakage tests, fixture-based feature tests, a real-match E2E. |
| IV. Honest Model Evaluation | Temporally-correct held-out split; explicit baseline on identical matches; MLflow tracks runs/metrics/params/artifacts; a model that loses to baseline is reported as such. | ✅ This is the feature's core; FR-002/004/005/006/008 enforce it. |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-winrate-predictor/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI + report schema)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
services/core/
├── alembic/versions/                  # migration: match outcome (winner + series score)
├── src/vct_moneyball/
│   ├── collect/parse.py               # + extract series score / winner (offline re-parse)
│   ├── store/models.py                # + match.winner_team_id, match.score_* (outcome)
│   ├── predict/                       # NEW — the winrate model
│   │   ├── labels.py                  # match outcome label from stored results
│   │   ├── features.py                # leakage-free pre-match feature builder
│   │   ├── dataset.py                 # temporal split + dataset assembly
│   │   ├── baselines.py               # explicit non-learned baselines
│   │   ├── model.py                   # train + calibrate; predict_proba
│   │   ├── evaluate.py                # log-loss, accuracy, Brier/calibration
│   │   └── tracking.py                # MLflow run wrapper + dataset/config fingerprint
│   └── cli/
│       ├── train_winrate.py           # vctm train-winrate
│       ├── predict_match.py           # vctm predict-match
│       └── eval_winrate.py            # vctm eval-winrate (temporal split vs baseline)
└── tests/
    ├── unit/                          # features (no leakage), labels, baselines, metrics
    ├── integration/                   # train/eval on fixtures + DB; split correctness
    └── fixtures/                      # cached match HTML incl. a known result

artifacts/
└── models/winrate/                    # committed evaluation reports (JSON + Markdown)
```

**Structure Decision**: Extend the existing single project under `services/core/`. A new
`predict/` package holds the model stages (labels → features → dataset/split → model →
evaluate → tracking), each independently testable, exposed through new `vctm` subcommands.
The only feature-001 change is additive: persist the match outcome (re-derived offline from
cached HTML) so labels exist. MLflow keeps run lineage; reports live in `artifacts/` like
the feature-001 rankings.

## Complexity Tracking

> No constitution violations — nothing to justify.
