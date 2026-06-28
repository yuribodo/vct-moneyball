# Feature Specification: ENC Roster-Strength Bridge (Phase 3)

**Feature Branch**: `003-roster-strength-bridge`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "Derive each ENC national team's strength from its active
roster's recent CLUB performance so the power ranking and winrate predictor can produce
confident, opponent-aware ENC outputs instead of ~50/50 low-confidence."

## Overview

Both shipped features stop at the same wall: a national team (e.g., "Brazil") has **no
match history as an entity** — it exists only as a roster of players who compete for clubs.
So the power ranking (001) leans on thin signals and the winrate predictor (002) honestly
abstains (~50/50, low-confidence) on ENC matchups. This feature **bridges** that gap: it
derives each ENC national team's strength from its active roster's recent **club**
performance (already collected), so a national team can be scored and matched up with
calibrated confidence. The bridge must be leakage-free, baseline-relative, and traceable —
and it must say "I don't know" when a roster's club history is too thin, rather than invent
confidence.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Confidently predict an ENC matchup (Priority: P1) 🎯 MVP

An analyst asks for "Brazil vs United States" and gets a **differentiated, calibrated**
win probability (not 50/50), because each team's strength is built from its players' recent
club form — using only information dated before the matchup.

**Why this priority**: This is the whole point — turn the honest abstention into a confident,
defensible ENC prediction. It is the smallest slice that delivers the missing value.

**Independent Test**: Request a prediction for two ENC teams as of a date; confirm the two
probabilities are differentiated (not both ~0.5), are flagged confident when both rosters
have enough club history, and that every input is dated before the as-of date.

**Acceptance Scenarios**:

1. **Given** two ENC teams whose rosters have sufficient recent club history, **When** a
   matchup is requested as of a date, **Then** the system returns calibrated, differentiated
   win probabilities (summing to 1.0) and the predicted winner, marked confident.
2. **Given** an ENC team whose roster has little recent club history, **When** a matchup is
   requested, **Then** the prediction is still returned but flagged low-confidence — never a
   fabricated certainty.

---

### User Story 2 - Rank the 16 ENC teams by roster-derived strength (Priority: P1)

The 16 ENC teams are ordered by a strength derived from their rosters' club performance,
giving an opponent-aware power ranking that no longer depends on non-existent national-team
matches.

**Why this priority**: It directly upgrades the feature-001 deliverable (the locked ranking)
with a defensible, data-backed national-team strength, and reuses the same locking/immutable
artifact discipline.

**Independent Test**: Produce a roster-derived ordering of the 16 ENC teams as of the lock
date; confirm all 16 are placed, each with a confidence label, using only pre-lock data.

**Acceptance Scenarios**:

1. **Given** the 16 ENC rosters and their players' club histories before the lock date,
   **When** a roster-derived ranking is built, **Then** all 16 teams are ordered with a
   per-team strength and confidence, traceable to the contributing players.

---

### User Story 3 - Prove roster-derived strength is honest and better than a baseline (Priority: P2)

A skeptic checks whether roster-derived strength actually predicts real outcomes better than
a simple baseline (the feature-001 roster-tier pedigree, or a naive average of player
ratings), evaluated on real matches the bridge did not see.

**Why this priority**: Per the constitution, a derived strength is only credible if it beats
an explicit baseline on held-out data, with no leakage.

**Independent Test**: On a held-out set of real team matches (e.g., club matches whose
rosters are known), score roster-derived strength vs. the baseline; confirm the comparison
is on identical matches, leakage-free, and reported even when the bridge loses.

**Acceptance Scenarios**:

1. **Given** a held-out evaluation set, **When** roster-derived strength and the baseline are
   scored, **Then** both are reported on the same matches and a bridge that does not beat the
   baseline is reported as such, not hidden.

---

### Edge Cases

- A roster player with **no** recent club history → contributes via a labeled low-confidence
  prior, never a guessed value; if too many roster players are sparse, the team is flagged
  low-confidence.
- Roster captured at lock time differs from who actually plays → strength uses the **active
  roster as recorded**, dated before the prediction.
- A player who recently changed clubs → only their pre-as-of club performance is used.
- Two ENC teams sharing no comparable competition history → the bridge still yields a
  strength (from each roster independently) and flags uncertainty appropriately.
- An ENC team whose entire roster is sparse → ranking still places it, clearly low-confidence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute, for an ENC national team and an as-of date, a strength
  (and/or feature vector) aggregated from its **active roster's** club performance using only
  data dated before the as-of date (no leakage).
- **FR-002**: System MUST feed roster-derived strength into the existing match predictor so
  an ENC matchup yields **differentiated**, calibrated win probabilities (not ~50/50) when
  rosters have sufficient history.
- **FR-003**: System MUST flag a team (and its prediction) low-confidence when its roster's
  club history is below a minimum-history threshold, representing sparse players with a
  transparent prior (reusing the existing confidence mechanism).
- **FR-004**: System MUST produce a roster-derived ordering of the 16 ENC teams with a
  per-team strength and confidence, usable by the feature-001 ranking artifact.
- **FR-005**: System MUST compare roster-derived strength against at least one explicit
  baseline (feature-001 roster-tier pedigree, or a naive average of player ratings) on
  held-out real matches, scored on the identical set.
- **FR-006**: System MUST report whether roster-derived strength beats the baseline (accuracy
  and a probabilistic score), and report a non-improvement honestly.
- **FR-007**: Every roster-derived strength and reported metric MUST be traceable to the
  contributing players, the data window, and the configuration that produced it.
- **FR-008**: Results MUST be reproducible from the same versioned inputs + configuration.
- **FR-009**: The capability MUST be exposed through the existing command-line interface,
  reusing the collect/store/predict layers; no new data collection is required for the MVP.
- **FR-010**: The bridge MUST NOT modify previously locked feature-001/002 artifacts; new
  outputs are new dated artifacts.

### Key Entities *(include if feature involves data)*

- **Roster snapshot**: the active players of an ENC team as recorded at the as-of date.
- **Player club strength**: a player's pre-as-of strength derived from their club matches
  (recent form/rating), with a volume-based confidence.
- **Roster-derived team strength**: the aggregate of a roster's player club strengths into a
  team rating/feature vector + a confidence label.
- **Bridge baseline**: an explicit non-derived rule (roster-tier pedigree, or naive player-
  rating average) the bridge is measured against.
- **Bridge evaluation**: per-metric bridge-vs-baseline values on held-out real matches,
  including sample size and leakage verification.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For ENC matchups where both rosters meet the history threshold, predictions are
  **differentiated** (the two probabilities differ by a meaningful margin, not ~50/50) and
  calibrated.
- **SC-002**: 100% of roster-derived strengths use only data dated before the as-of date
  (zero leakage), verified automatically.
- **SC-003**: All 16 ENC teams receive a roster-derived strength and an explicit confidence
  label; sparse rosters are labeled low-confidence rather than dropped or guessed.
- **SC-004**: Roster-derived strength is reported beside at least one baseline on the same
  held-out matches; a non-improvement is reported as such.
- **SC-005**: Any roster-derived strength can be traced to the contributing players, data
  window, and configuration.
- **SC-006**: Re-running with the same versioned inputs/config reproduces the strengths and
  metrics exactly.

## Assumptions

- The data source is the existing feature-001/002 schema (rosters, players, club matches,
  outcomes); no new scraping is required for the MVP.
- "Club performance" reuses the feature-002 leakage-free signals (Elo/form/volume) computed
  for the players' clubs, attributed to players via their participation.
- The honest evaluation set is **real team matches with known rosters** (club matches), since
  ENC national-team results do not exist yet; the bridge's value is established there and then
  applied to the ENC cohort.
- Prediction unit remains the match (series) winner; the bridge supplies team strength as the
  input, not a new label.
- Baselines available now include the feature-001 roster-tier pedigree and a naive average of
  player ratings.
