# Feature Specification: ENC Prediction API (Phase 4)

**Feature Branch**: `004-prediction-api`

**Created**: 2026-06-28

**Status**: Draft

**Input**: User description: "A read-only serving layer that exposes the locked ENC power
rankings, on-demand ENC matchup predictions, and the honest evaluation results so a client
(e.g., a future web demo) can consume them — reusing the existing pipeline, with the same
honesty (confidence, provenance, traceability) and no mutation."

## Overview

Features 001–003 produce locked rankings, a winrate predictor, and confident roster-derived
ENC predictions — but they are only reachable through the CLI and committed files. This
feature makes them **consumable over a network**: a read-only service that serves the locked
ENC rankings, answers live ENC matchup questions, and exposes the honest evaluation results,
carrying the same confidence flags, provenance, and traceability. It mutates nothing — locked
artifacts are served exactly as published — and its answers match the CLI for the same inputs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the ENC rankings over the network (Priority: P1) 🎯 MVP

A client requests the current ENC power ranking and receives the 16 ordered teams with
scores/strength, confidence, and which published artifact it came from.

**Why this priority**: Serving the locked ranking is the smallest slice that makes the
project's headline output consumable by anything other than the CLI.

**Independent Test**: Request the ranking; confirm 16 teams in order, each with a confidence
label, plus the source artifact version/date — and that it byte-faithfully reflects the
locked artifact (no re-computation, no mutation).

**Acceptance Scenarios**:

1. **Given** a published ENC ranking, **When** a client requests it, **Then** the service
   returns the 16 ordered teams with scores, confidence, and the artifact version it served.
2. **Given** no published ranking exists, **When** a client requests it, **Then** the service
   responds with a clear "not found" result, not an error or an empty success.

---

### User Story 2 - Predict an ENC matchup over the network (Priority: P1)

A client asks "who wins, Team A vs Team B, as of a date" and gets calibrated win
probabilities, the predicted winner, a confidence flag, and the top contributing players.

**Why this priority**: The live prediction is the project's most interactive value; exposing
it is what a demo needs.

**Independent Test**: Request a matchup; confirm two probabilities summing to 1.0, a winner,
a confidence flag, and that the result is identical to the CLI for the same inputs.

**Acceptance Scenarios**:

1. **Given** two resolvable ENC teams and a date, **When** a client requests a prediction,
   **Then** the service returns calibrated win probabilities, the winner, a confidence flag,
   and the top contributors.
2. **Given** an unknown team or a malformed date, **When** a client requests a prediction,
   **Then** the service returns a clear client-error result (not a server crash).
3. **Given** a team whose roster history is sparse, **When** a prediction is requested,
   **Then** the response is flagged low-confidence — never a fabricated certainty.

---

### User Story 3 - Read the honest evaluation results (Priority: P2)

A client retrieves how the models scored against their baselines (the published evaluation
reports), so the predictions can be judged, not just consumed.

**Why this priority**: The project's credibility rests on honest, baseline-relative results
(Constitution IV); exposing them keeps the served predictions accountable.

**Independent Test**: Request the latest evaluation; confirm per-metric model-vs-baseline
values, the data window, and the run/fingerprint it came from.

**Acceptance Scenarios**:

1. **Given** a published evaluation report, **When** a client requests it, **Then** the
   service returns the per-metric model-vs-baseline values with the run id and data window.

---

### Edge Cases

- The service starts with no published artifacts / no collected data → endpoints respond with
  clear "not found"/"unavailable" results, never a crash or a misleading empty success.
- The database is unreachable → the service reports a clear unavailable status; it never
  invents data.
- A prediction request for two teams not in the cohort → clear client error.
- Concurrent requests → answers remain consistent and read-only (no shared mutable state
  corrupts results).
- A locked artifact on disk is malformed → the service surfaces the problem rather than
  serving partial/garbled data.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The service MUST serve the locked ENC power ranking (the 16 ordered teams with
  scores/strength + confidence) exactly as published, identifying the source artifact, and
  MUST NOT recompute or mutate it.
- **FR-002**: The service MUST answer a live ENC matchup prediction (calibrated win
  probabilities, winner, confidence flag, top contributors) for two resolvable teams and a
  date, reusing the existing prediction pipeline.
- **FR-003**: A prediction whose rosters are below the history threshold MUST be flagged
  low-confidence; the service never fabricates certainty (reuses the existing confidence rule).
- **FR-004**: The service MUST expose the honest evaluation results (per-metric
  model-vs-baseline values, data window, run id/fingerprint) from the published reports.
- **FR-005**: For identical inputs, a prediction returned by the service MUST equal what the
  CLI produces (the service is a thin transport over the same logic).
- **FR-006**: The service MUST be read-only: no endpoint mutates collected data, locked
  artifacts, or runs.
- **FR-007**: Invalid requests (unknown team, malformed date) MUST return a clear client-error
  result; unavailable dependencies (no data, DB down) MUST return a clear unavailable result —
  never a crash or a misleading success.
- **FR-008**: Every served ranking/prediction/evaluation MUST carry its provenance/traceability
  (artifact version or run id + data window/fingerprint) so a consumer can audit it.
- **FR-009**: Responses MUST be machine-readable (structured) and documented so a client (e.g.,
  a future web demo) can integrate without reading the source.
- **FR-010**: The service MUST be reproducible and testable headlessly (no external services
  required beyond the existing database).

### Key Entities *(include if feature involves data)*

- **Served ranking**: the published ENC ordering (teams, scores/strength, confidence) + its
  source artifact identity.
- **Prediction request/response**: the two teams + date in; probabilities, winner, confidence,
  and top contributors out, with provenance.
- **Served evaluation**: the published per-metric model-vs-baseline results + run identity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A client can retrieve the 16-team ENC ranking and a matchup prediction without
  using the CLI or reading files.
- **SC-002**: A prediction returned by the service is identical to the CLI's for the same
  inputs (verified).
- **SC-003**: Typical ranking/prediction requests return in under 1 second.
- **SC-004**: 100% of served ranking/prediction/evaluation responses carry provenance
  (artifact version or run id + window/fingerprint).
- **SC-005**: Invalid or unavailable requests return a clear, correct status (client vs.
  server vs. not-found) in 100% of the tested cases — never a crash or misleading success.
- **SC-006**: Low-confidence predictions are flagged as such; no response presents an
  unjustified confident result.
- **SC-007**: No request mutates any stored data, locked artifact, or run (verified).

## Assumptions

- The serving layer reuses the existing feature-001/002/003 logic and the same database; it
  introduces no new modeling and no new data collection.
- The MVP is the API (machine-readable responses); a human-facing web demo (e.g., Next.js)
  that consumes it is a later phase.
- "Current ranking" defaults to the most recent published ENC artifact (the roster-derived
  one), with the locked power ranking also retrievable.
- Live predictions are computed on request from the existing pipeline (deterministic), not
  precomputed; typical scope keeps this well under a second.
- Authentication/rate-limiting are out of scope for the MVP (local/trusted use); the service
  is read-only so the risk surface is small.
