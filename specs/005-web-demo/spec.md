# Feature Specification: ENC Web Demo (Phase 5)

**Feature Branch**: `005-web-demo`

**Created**: 2026-06-28

**Status**: Draft

**Input**: "A small Next.js web demo that consumes the feature-004 prediction API so a human
can read the ENC power ranking, get a matchup win probability, and see the honest evaluation
— the public face of the Moneyball thesis."

## Overview

Features 001–004 produce the data, predictions, and a read-only API. This feature is the
**human-facing demo**: a small Next.js site that consumes the API and presents the project's
story — the locked ENC ranking, a live matchup predictor, and the honest "who was right"
evaluation. It adds no business logic and no data; it is a presentation layer over the API,
preserving its honesty (confidence flags, provenance, "model vs. baseline").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the ENC power ranking (Priority: P1) 🎯 MVP

A visitor lands on the site and sees the 16 ENC teams ranked, each with its strength and a
confidence label, plus which dated artifact it came from.

**Independent Test**: Load the home page against a running API; the 16 teams render in order
with confidence and the source version; if the API is down, a clear message shows (no blank
crash).

**Acceptance Scenarios**:

1. **Given** a published ranking, **When** the home page loads, **Then** the 16 ordered teams
   render with strength + confidence and the artifact version.
2. **Given** the API is unreachable, **When** the page loads, **Then** a clear "unavailable"
   message shows instead of an error page.

---

### User Story 2 - Predict a matchup (Priority: P1)

A visitor picks two ENC teams and a date and sees the win probabilities, the predicted
winner, the top contributing players, and a low-confidence note when applicable.

**Independent Test**: Choose two teams and submit; the page shows two probabilities summing to
100%, the winner, contributors, and a low-confidence badge when the API flags it.

**Acceptance Scenarios**:

1. **Given** two ENC teams, **When** the visitor requests a prediction, **Then** the page
   shows calibrated probabilities, the winner, and the top contributors.
2. **Given** a sparse-roster team, **When** a prediction returns, **Then** the UI shows the
   low-confidence note — it never presents a false certainty.

---

### User Story 3 - See "who was right" (the honest evaluation) (Priority: P2)

A visitor views how the model scored against its baseline on held-out matches, so the
predictions are accountable, not just flashy.

**Independent Test**: Open the evaluation view; per-metric model-vs-baseline values render with
the run it came from.

**Acceptance Scenarios**:

1. **Given** a published evaluation, **When** the visitor opens the page, **Then** the
   model-vs-baseline metrics render with the run id and whether the model beat its baseline.

---

### Edge Cases

- API unreachable / endpoint 404 → a clear, friendly "unavailable / not published yet" state,
  never a blank screen or a stack trace.
- A prediction error (unknown team / bad date) → an inline, readable message.
- Slow API → a loading state, not a frozen page.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The site MUST display the ENC ranking from the API (16 teams, strength,
  confidence, source version).
- **FR-002**: The site MUST let a visitor request a matchup prediction (two teams + date) and
  show probabilities, winner, confidence, and top contributors from the API.
- **FR-003**: The site MUST display the honest evaluation (model-vs-baseline metrics + run).
- **FR-004**: The site MUST preserve the API's honesty: confidence flags and "model vs.
  baseline" framing are shown, never hidden.
- **FR-005**: The site MUST handle API failures/empties gracefully with clear states (no blank
  crash, no stack trace).
- **FR-006**: The site MUST add no business logic — it only reads and renders the API; the API
  base URL is configurable.
- **FR-007**: The site MUST build cleanly (production build succeeds, types check).

### Key Entities *(include if feature involves data)*

- **View models**: thin client-side shapes mirroring the API responses (ranking, prediction,
  evaluation) — no new data, just presentation.

## Success Criteria *(mandatory)*

- **SC-001**: A visitor can read the 16-team ranking and get a matchup prediction in the
  browser, without the CLI.
- **SC-002**: Confidence and "model vs. baseline" framing are visible on the relevant views.
- **SC-003**: When the API is down or an endpoint is empty, the UI shows a clear state (100% of
  tested failure cases) — never a blank crash.
- **SC-004**: The production build succeeds and types check.

## Assumptions

- Consumes the feature-004 API (read-only); adds no data or modeling.
- Next.js (the constitution's named demo stack); minimal dependencies; styling is clean and
  legible (a full design system is out of scope for the MVP).
- Visual/interaction QA is performed by a human in a browser (headless build + type checks are
  the automated gate here); the API is assumed running locally.
- Authentication and deployment are out of scope for the MVP (local demo).
