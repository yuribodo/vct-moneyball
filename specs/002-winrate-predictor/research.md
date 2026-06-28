# Phase 0 Research: Match Winrate Predictor (Phase 2)

Decisions resolving the technical unknowns. Each records the decision, why, and the
alternatives rejected.

## R1. Learner — regularized, calibrated logistic regression (GBT optional)

**Decision**: The MVP model is an L2-regularized **logistic regression** over
opponent-difference features, wrapped in probability **calibration**
(`CalibratedClassifierCV`, isotonic/sigmoid chosen by validation). Gradient-boosted trees
(XGBoost/LightGBM, already available) are supported as a tracked alternative learner behind
the same interface.

**Rationale**: With ~1k–5k matches and a handful of features, a linear model is hard to
overfit, is transparent (coefficients explain each side's edge), and calibrates cleanly to
probabilities — matching the constitution's "explainable, honest" bias (R1 of feature 001
in spirit). GBT is kept available for when data/features grow, but is not the default.

**Alternatives**: GBT as default (overfits small data, opaque); a bespoke Elo/Bradley-Terry
rating only (good but ignores rich per-player features) — Elo is instead used as a *feature*
and a *baseline* (R6).

## R2. Features — symmetric opponent-difference signals, leakage-free

**Decision**: For a match between A and B at time *t*, compute each signal for A and B from
data strictly before *t*, then encode the example as the **difference** `f(A) − f(B)` (plus
a global side indicator), so the model is symmetric and a single row represents the matchup.
Signals (all as-of *t*):

- **Recent form**: trailing mean of the team's per-map player composite (reuse feature-001
  scoring) over a configurable look-back.
- **Opponent-adjusted strength**: a chronologically-updated team rating (Elo-style) and/or
  the feature-001 power-ranking team score computed on pre-*t* data.
- **Map history**: team map win-rate before *t* (needs the new outcome label, R4).
- **Head-to-head**: prior A-vs-B results before *t* (sparse; smoothed).
- **Roster pedigree**: average club-tier of the team's active players (the feature-001
  `roster-tier-seed` signal).
- **Experience/volume**: number of in-window maps before *t* (drives the confidence flag).

**Rationale**: Differences make the model side-agnostic and halve parameters; reusing
feature-001 scoring keeps lineage. Every signal is a pure as-of function → testable for
leakage (R3).

**Alternatives**: Raw per-side features (doubles params, asymmetric); deep player embeddings
(Phase 3 — too heavy/opaque now).

## R3. Leakage prevention — as-of features + verified temporal split

**Decision**: Features are built by an **as-of** query that, for each match, only reads rows
with `played_at < match.played_at` (and capture time before, where relevant). The dataset
builder asserts, per example, that no contributing row is dated on/after the match. The
train/eval split is a single forward-chaining **cutoff**: train = matches before cutoff,
eval = matches on/after; the builder verifies zero overlap and that no match straddles the
split (a match is atomic). A unit test feeds a match with a deliberately "future" stat and
asserts it is excluded.

**Rationale**: Directly implements FR-002/FR-004 and SC-001 — leakage is the single biggest
way to fool yourself in sports prediction (Constitution IV). Verification, not trust.

**Alternatives**: Random k-fold (leaks future→past; rejected); per-row timestamp filtering
only without the atomic-match guard (a Bo3 could split across the cutoff).

## R4. Outcome label — series result re-derived offline from cached HTML

**Decision**: Persist each match's **winner** and **series score** (e.g., 2–1). Feature 001
captured per-map player stats but not the result; extend `collect/parse.py` to read the
match-header series score (and per-map winners) and add `match.winner_team_id` +
`match.score_a/score_b` via an Alembic migration. Because feature 001 caches raw HTML, this
is an **offline re-parse** — no new scraping. The match label = the team that won the series
(majority of maps when the explicit score is absent).

**Rationale**: A winrate predictor needs ground-truth outcomes; deriving them offline keeps
provenance (Constitution I) and reproducibility. The header score is the authoritative
result.

**Alternatives**: Infer winner purely from per-map `winner_team_id` (often null in current
data); re-scrape (disrespectful, unnecessary given the cache).

## R5. Evaluation — forward-chaining split, probabilistic metrics

**Decision**: Report **log-loss** (primary), **accuracy**, and **Brier score** +
a reliability/calibration summary, on the held-out future block. Support an optional
**rolling-origin** evaluation (several successive cutoffs) for a more stable estimate, with a
sample-size warning when a fold is underpowered.

**Rationale**: Log-loss/Brier reward honest probabilities (not just labels), and calibration
is a stated requirement (SC-003). Forward-chaining mirrors how the model is actually used.

**Alternatives**: Accuracy alone (ignores confidence/calibration); a single tiny holdout (high
variance — hence the optional rolling-origin).

## R6. Baselines — explicit, non-learned, scored on identical matches

**Decision**: Provide at least these baselines, each producing a probability/label on the
same eval matches: (a) **roster-tier pedigree** (feature-001 `roster-tier-seed`), (b)
**favorite by prior power ranking** (the locked feature-001 ranking), (c) **historical
win-rate / Elo** updated chronologically. The model is reported beside ≥1 baseline; losing to
it is reported, not hidden (FR-005/FR-006).

**Rationale**: A number without a baseline is meaningless (Constitution IV). These are cheap,
transparent, and reuse feature-001 outputs.

**Alternatives**: No baseline (forbidden); only a 50/50 coin baseline (too weak to be honest).

## R7. Tracking — MLflow local file store + dataset/config fingerprint

**Decision**: Use **MLflow** with a local file store (`mlruns/`, git-ignored). Each run logs
params (learner, look-backs, cutoff), metrics (model + baselines), the data-window bounds, a
**dataset+feature+config fingerprint** (hash), and the model artifact + the eval report.
Reports are also written to `artifacts/models/winrate/` as committed JSON + Markdown.

**Rationale**: Implements FR-008/SC-005 — every reported number traces to the exact run.
MLflow is the constitution's designated tracker.

**Alternatives**: Ad-hoc CSV logs (no lineage); a DB table for runs (reinvents MLflow).

## Open items (data, validated at runtime)

- Coverage of the new winner field across the ~1,133 already-cached matches (some pages may
  lack a parseable series score → those matches are unlabeled and excluded from training,
  logged, never guessed).
- Whether map-level `winner_team_id` is reliable enough to add map win-rate features, or only
  series-level outcomes are used in the MVP.
