# Feature Specification: Match Winrate Predictor (Phase 2)

**Feature Branch**: `002-winrate-predictor`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Phase 2 — a model that predicts the outcome and win
probability of a professional Valorant match between two teams, from features derived
from the already-collected per-map player/team history (feature 001). Temporally-correct
splits (no leakage), compared against an explicit baseline, with traceable training runs."

## Overview

Feature 001 produces a transparent power ranking, but it has no notion of *who beat
whom* — it cannot say "Team A beats Team B with 64% probability," and its ordering
ignores opponent strength. This feature learns match outcomes directly from history so
predictions are **earned on data the model has never seen** and are reported honestly
against a baseline (Constitution IV). It reuses the feature-001 collection/storage layer
(Postgres, provenance) as its data source; no new scraping is required.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Predict a match before it is played (Priority: P1) 🎯 MVP

An analyst names two teams and a match date and gets each team's win probability, derived
only from information available **before** that date.

**Why this priority**: This is the core product — a falsifiable, opponent-aware
prediction the power ranking cannot give. It is the smallest slice that delivers value.

**Independent Test**: Train on matches up to a cutoff, then ask the model for a held-out
future match's probabilities; confirm two probabilities that sum to 1 and that no feature
used any data dated on/after the match.

**Acceptance Scenarios**:

1. **Given** a trained model and two teams with sufficient pre-match history, **When** a
   prediction is requested for a future match, **Then** the system returns calibrated win
   probabilities for both sides that sum to 1.0 and names the predicted winner.
2. **Given** a team with little or no pre-match history, **When** a prediction is
   requested, **Then** the system still returns a probability and flags it low-confidence
   (never invents certainty the data does not support).

---

### User Story 2 - Prove the model is honest (leakage-free, beats a baseline) (Priority: P1)

A skeptic runs an evaluation that trains on past matches, predicts a block of **future**
matches the model never saw, and reports accuracy, log-loss, and calibration against an
explicit baseline.

**Why this priority**: Per the constitution, a model claim is worthless without a
temporally-correct split and a baseline. This is what makes the prediction credible.

**Independent Test**: Run the evaluation on a temporal split; confirm every evaluated
match is dated strictly after every training match, the baseline is scored on the same
matches, and a report states whether the model beats the baseline on log-loss.

**Acceptance Scenarios**:

1. **Given** a temporal cutoff, **When** evaluation runs, **Then** training uses only
   matches before the cutoff and evaluation uses only matches on/after it, with zero
   overlap, and this is verified, not assumed.
2. **Given** an evaluation run, **When** results are reported, **Then** the model's
   log-loss and accuracy are shown side-by-side with at least one explicit baseline's,
   and a model that does not beat its baseline is reported as such — not hidden.
3. **Given** the same versioned inputs and configuration, **When** evaluation is re-run,
   **Then** the reported metrics are identical (reproducible).

---

### User Story 3 - Trace every reported number to its run (Priority: P2)

A reviewer can point at any reported metric and recover the exact data window, features,
parameters, and code/config version that produced it.

**Why this priority**: Traceability (Constitution I/IV) lets a number be defended or
refuted later; without it, results are anecdotes.

**Independent Test**: Run two trainings with different parameters; confirm each run is
recorded with its params, metrics, data window, and a config/feature fingerprint, and the
two are distinguishable and retrievable.

**Acceptance Scenarios**:

1. **Given** a completed training+evaluation, **When** the reviewer inspects the run
   record, **Then** it contains the data window, baseline, feature/version fingerprint,
   parameters, and all reported metrics.

---

### Edge Cases

- A match where one or both teams have **no** in-window history before the match date →
  prediction falls back to a labeled low-confidence prior; never errors silently.
- The temporal cutoff lands between two maps of the same match → the whole match is
  assigned to exactly one side of the split (a match is never split across train/eval).
- Roster changes: a team's pre-match strength is computed from the players active at that
  time, not a later roster.
- Too few future matches to evaluate → the run reports an underpowered-sample warning
  rather than a falsely precise score.
- A feature that could encode the result (final score, post-match rating) is rejected at
  build time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST learn a match-outcome model from historical professional
  matches stored by feature 001, using only the collected, provenance-bearing data.
- **FR-002**: System MUST build each match's features from information dated strictly
  **before** that match; any feature derivable only from the match's own result is
  prohibited and MUST be rejected (no leakage — Constitution IV).
- **FR-003**: System MUST output, for a given matchup and date, a win probability per
  side that sums to 1.0, plus the predicted winner.
- **FR-004**: System MUST evaluate using a **temporally-correct split** — train strictly
  before a cutoff, evaluate strictly on/after — and MUST verify (not assume) zero overlap
  and no cross-split match.
- **FR-005**: System MUST compare every model against at least one **explicit baseline**
  (e.g., roster-tier pedigree from feature 001, or historical head-to-head/map win-rate),
  scored on the identical evaluation matches.
- **FR-006**: System MUST report accuracy, log-loss, and a calibration measure for both
  the model and the baseline, and MUST state plainly when the model does not beat the
  baseline.
- **FR-007**: System MUST flag predictions for teams below a minimum-history threshold as
  low-confidence and represent them with a transparent prior.
- **FR-008**: System MUST record each training/evaluation run with its data window,
  feature/config fingerprint, parameters, baseline, and metrics, so any reported number
  is traceable to the run that produced it.
- **FR-009**: Results MUST be reproducible: the same versioned inputs + configuration
  yield identical metrics.
- **FR-010**: System MUST expose train and evaluate operations through the existing
  command-line interface, with machine-readable output available.
- **FR-011**: The locked power-ranking artifacts from feature 001 MUST be usable as one
  baseline ("favorite by prior power ranking") without being modified.

### Key Entities *(include if feature involves data)*

- **Training example**: one historical match reduced to a label (which side won) plus a
  feature vector built only from pre-match information.
- **Feature set**: the named, versioned set of pre-match signals (e.g., recent form,
  opponent-adjusted strength, map history) with a fingerprint for traceability.
- **Model run**: a single train+evaluate execution — its data window, parameters,
  baseline, metrics, and artifact reference.
- **Baseline**: an explicit, non-learned ordering/probability rule the model must beat.
- **Evaluation report**: per-metric model-vs-baseline values on the held-out future set,
  including calibration and sample size.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of evaluated matches are dated strictly after every training match
  (zero temporal leakage), verified automatically each run.
- **SC-002**: Every reported metric is accompanied by at least one baseline's value on
  the same matches; a model below baseline is reported as a non-result.
- **SC-003**: Predictions are probabilities (sum to 1.0) with a measured calibration
  error, not bare labels.
- **SC-004**: Re-running an evaluation on the same versioned inputs/config reproduces the
  reported metrics exactly.
- **SC-005**: Any reported number can be traced to a stored run carrying its data window,
  feature/config fingerprint, parameters, and baseline.
- **SC-006**: On a held-out future block, the model's log-loss is reported against the
  baseline's, establishing whether the learned model adds predictive value over the
  feature-001 prior.
- **SC-007**: A prediction involving a team with insufficient history is always returned
  with a low-confidence flag rather than an error or an unjustified confident output.

## Assumptions

- The data source is the existing feature-001 Postgres schema; no new collection is
  required for the MVP (the model consumes already-collected matches/maps/stats).
- Prediction unit is the **match** (series) winner; per-map signals may be inputs but the
  predicted label is which team wins the match.
- Professional matches collected in the data window are the universe; the model is
  general (not ENC-only) so it can also rank/forecast the ENC cohort.
- "Outcome" is binary (one side wins) — Valorant matches do not draw at the series level.
- Experiment tracking and the modeling toolkit follow the constitution's stack (MLflow
  for tracking; the specific learner is a planning decision, not a spec concern).
- Baselines available at lock time include the feature-001 roster-tier pedigree and a
  historical win-rate rule; at least one is used.
