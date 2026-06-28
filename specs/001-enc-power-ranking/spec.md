# Feature Specification: ENC 2026 Power Ranking (MVP)

**Feature Branch**: `001-enc-power-ranking`

**Created**: 2026-06-27

**Status**: Draft

**Input**: User description: "MVP — ENC 2026 Power Ranking: scrape VLR.gg, model each player per map, score and publish a public ranking of the 16 ENC national teams with per-map breakdown, locked and dated before the Riyadh tournament in November."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the ENC team power ranking (Priority: P1)

A Valorant fan, analyst, or coach opens the published ranking and sees the 16
national teams competing at ENC 2026 ordered from strongest to weakest, each with
a per-map breakdown showing how strong the team is on every competitive map.

**Why this priority**: This is the entire deliverable of the MVP and the project's
first public claim. If only this story ships, the project still delivers value: a
defensible, data-driven answer to "who are the best ENC teams, and on which maps?"

**Independent Test**: Open the published ranking artifact and confirm it lists
exactly 16 teams in a definite order, each with a per-map strength breakdown and a
visible position. No other feature is required for this to be useful.

**Acceptance Scenarios**:

1. **Given** the ranking has been published, **When** a reader opens it, **Then**
   they see exactly 16 ENC 2026 national teams in a strict order from 1 to 16.
2. **Given** a team in the ranking, **When** the reader inspects it, **Then** they
   see a per-map breakdown covering each map in the competitive pool.
3. **Given** a team's position, **When** the reader asks "why is this team here?",
   **Then** they can see which players and per-map values drove that team's score.

---

### User Story 2 - Trust that the prediction was locked before kickoff (Priority: P1)

A skeptical reader wants to confirm the ranking is a genuine prediction, not a
hindsight edit. They check that the published ranking carries a publication date
that precedes the first ENC 2026 match in Riyadh and has not been altered since.

**Why this priority**: A power ranking that can be quietly changed after games are
played proves nothing. The credibility of the whole project depends on the
prediction being frozen and dated before the event. This is co-critical with US1.

**Independent Test**: Inspect the published ranking and confirm it has a
publication timestamp earlier than the tournament start, and that the artifact is
immutable (any later revision is a separate, dated artifact that cites the original).

**Acceptance Scenarios**:

1. **Given** the tournament start (first ENC 2026 match) is known, **When** the
   ranking is published, **Then** its publication timestamp is at least 1 full day
   before the tournament start.
2. **Given** a published ranking, **When** a correction is needed, **Then** a new
   dated artifact is issued that references the superseded one, and the original
   remains unchanged and visible.
3. **Given** any data point behind the ranking, **When** someone asks where it came
   from, **Then** its source reference and capture time can be produced so the
   ranking can be reproduced.

---

### User Story 3 - Settle the bet after the tournament (Priority: P2)

After ENC 2026 concludes, a reader compares the locked ranking against the actual
tournament results to see how accurate the prediction was — right or wrong.

**Why this priority**: This closes the Moneyball loop ("when it's over, the data
shows who was right"). It is essential to the project's mission but not required to
ship the pre-tournament MVP, so it is one tier below the published ranking itself.

**Independent Test**: Given the final ENC standings and the locked ranking, produce
an accuracy comparison (e.g., how closely predicted order matched actual order)
without modifying the original ranking.

**Acceptance Scenarios**:

1. **Given** final tournament standings, **When** the comparison is run, **Then** it
   reports the agreement between predicted and actual ordering using a stated metric.
2. **Given** the comparison, **When** a reader reviews it, **Then** the original
   locked ranking is referenced unchanged as the basis of the evaluation.

---

### Edge Cases

- **Roster not finalized / new players**: an ENC team includes a player with little
  or no professional match history at publication time — such players are represented
  by a labeled low-confidence baseline, not an invented strength (FR-012).
- **Map pool change**: a map is added to or removed from the competitive pool
  between data collection and publication.
- **Sparse map data**: a team has played very few professional matches on a given
  map, making its per-map strength low-confidence.
- **Source unavailable / changed**: the match-history source is unreachable or its
  data layout changes during collection.
- **Ties**: two teams compute to the same aggregate score and must still be placed
  in a strict 1–16 order.
- **Roster change after publication**: a team swaps a player after the ranking is
  locked — the locked artifact is not edited; this is reported as prediction risk.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST produce a ranking of exactly the 16 national teams
  competing at ENC 2026, in a strict order from 1 to 16 with no ties left unresolved.
- **FR-002**: System MUST score each rostered player's contribution on a per-map
  basis, derived from historical professional match data.
- **FR-003**: System MUST aggregate player scores into a single team strength score
  that determines each team's position in the ranking.
- **FR-004**: System MUST present, for each team, a per-map breakdown showing the
  team's relative strength on each map in the competitive pool.
- **FR-005**: System MUST make each team's position explainable — a reader can trace
  the position to the contributing players and per-map values.
- **FR-006**: The published ranking MUST be a dated artifact carrying a publication
  timestamp.
- **FR-007**: The published ranking MUST be released at least 1 full day (24h) before
  the **tournament start** — i.e., the first ENC 2026 match in Riyadh. ("Tournament
  start" is the canonical term for this deadline across all artifacts.)
- **FR-008**: Once published, a ranking artifact MUST be immutable; any correction is
  issued as a new dated artifact that references the artifact it supersedes, leaving
  the original intact and visible.
- **FR-009**: System MUST record the provenance of every data point used (source
  reference plus capture time) so any published ranking can be reproduced from
  versioned inputs.
- **FR-010**: System MUST attach a confidence indication to scores that rest on
  sparse data (few matches, limited map history, or limited player history).
- **FR-011**: System MUST support, after the tournament, comparing a locked ranking
  against actual results and reporting the agreement using a stated metric.
- **FR-012**: System MUST score only players who have sufficient professional match
  history; players below that threshold MUST be represented by a transparent,
  clearly-labeled low-confidence baseline rather than an invented strength value, and
  their contribution MUST be flagged as low-confidence wherever it affects a team's
  score. (The minimum-history threshold is a planning detail, fixed and recorded once
  chosen.)

### Key Entities *(include if feature involves data)*

- **Team**: one of the 16 ENC 2026 national teams; has a roster, an aggregate
  strength score, a ranking position, and a per-map breakdown.
- **Player**: a member of a team's roster; has a per-map contribution score and a
  data-confidence level reflecting how much history backs it.
- **Map**: a map in the competitive pool; the unit along which player and team
  strength is broken down.
- **Match (historical)**: a past professional game used as evidence; carries a source
  reference and capture time for provenance.
- **Ranking artifact**: the published, dated, immutable output — the ordered list of
  16 teams with per-map breakdowns and the data lineage behind them.
- **Outcome comparison**: the post-tournament evaluation that scores the locked
  ranking against actual ENC results.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The ranking covers 100% of the 16 ENC 2026 teams, each placed in a
  unique position from 1 to 16.
- **SC-002**: Every team shows a per-map breakdown covering 100% of the maps in the
  competitive pool.
- **SC-003**: The ranking is published with a timestamp at least 1 day before the
  first ENC 2026 match.
- **SC-004**: 100% of the ranking's data points can be traced to a recorded source
  and capture time, and the published ranking can be regenerated from versioned
  inputs without re-collecting data.
- **SC-005**: A reader can determine, for any team, the players and per-map values
  that produced its position without needing assistance.
- **SC-006**: After the tournament, an accuracy comparison against actual results can
  be produced for the locked ranking using a stated metric.
- **SC-007**: Any score backed by sparse data is visibly marked as low-confidence, so
  no reader mistakes a thin estimate for a well-supported one.

## Assumptions

- **Data source**: player and match history come from publicly available
  professional Valorant match records (VLR.gg). The published ranking is the
  project's first public artifact and is released in the project's public repository
  as a committed, dated file (a richer public presentation is a later phase).
- **Data window**: scoring uses recent professional play (assumed roughly the last
  ~12 months of relevant competition); the exact window is a planning detail and may
  be refined, but it is fixed and recorded once chosen.
- **Map pool**: the competitive map pool in effect at the time of data collection is
  used; a pool change before publication is handled by re-running collection.
- **Rosters**: each team is scored using its best-known roster at publication time;
  roster changes after publication are not retrofitted into the locked artifact.
- **Audience**: readers are Valorant-literate (fans, analysts, coaches) and
  understand maps, roles, and standings; no onboarding is assumed.
- **Out of scope for this MVP** (later phases): win-probability prediction for
  specific matchups, optimal 5th-player suggestion, roster optimization, the
  interactive web demo, and live drift monitoring.
