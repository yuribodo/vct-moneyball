# Implementation Plan: ENC Web Demo (Phase 5)

**Branch**: `005-web-demo` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

## Summary

A small **Next.js (App Router)** site under `web/` that consumes the feature-004 read-only
API and presents the project's story: the ENC ranking, a live matchup predictor, and the
honest evaluation. Server components fetch from the API (base URL via env), with graceful
"unavailable" states. No business logic, no data — a presentation layer that preserves the
API's honesty. The automated gate is a clean production build + type check; visual/interaction
QA is a human-in-browser step (the Chrome automation is not connected in this environment).

## Technical Context

**Language/Version**: TypeScript, Next.js 15 (App Router), React 19, Node ≥ 20.

**Primary Dependencies**: `next`, `react`, `react-dom`, TypeScript. Plain CSS (no UI framework)
to keep installs minimal and the build reliable. `fetch` for API calls.

**Storage**: none — reads the feature-004 API only. API base URL via `NEXT_PUBLIC_API_BASE`
(default `http://127.0.0.1:8000`).

**Testing**: `next build` (production build) + `tsc --noEmit` (type check) as the headless
gate; a typed API client centralizes the contract. Interaction/visual QA is manual in a
browser.

**Target Platform**: Browser (local dev via `next dev`; `next build`/`next start` for prod).

**Project Type**: Web frontend in `web/`, separate from the Python `services/core/`.

**Constraints**: Read-only consumer; graceful failure states (no blank crash); honesty
preserved (confidence + baseline framing shown); minimal deps; clean build.

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Reproducible Data Provenance | Renders the API's provenance (artifact version / run id) on each view; adds no data. | ✅ |
| II. Falsifiable, Locked Predictions | Displays locked artifacts via the API unchanged; never edits them. | ✅ |
| III. Test-First & E2E Validation | The headless gate is a green production build + type check; a typed client encodes the contract; visual QA is a documented human step. | ✅ (adapted for a frontend) |
| IV. Honest Model Evaluation | Surfaces "model vs. baseline" + confidence flags prominently; never hides a non-improvement. | ✅ |

**Result**: PASS — Constitution III is satisfied via build/type gates (a frontend's analogue
of the pipeline's pytest), with human visual QA documented; no violations.

## Project Structure

```text
web/
├── package.json · tsconfig.json · next.config.mjs · .env.example
├── lib/api.ts                 # typed API client (ranking/predict/evaluation) + base URL
├── app/
│   ├── layout.tsx · globals.css · page.tsx        # home = ranking
│   ├── predict/page.tsx                            # matchup predictor
│   └── honesty/page.tsx                            # model-vs-baseline evaluation
└── components/                # RankingTable, MatchupForm, MetricTable, States (loading/error)
```

**Structure Decision**: A standalone Next.js App-Router project in `web/` (kept separate from
the Python service). A single typed `lib/api.ts` is the only place that knows the API shape, so
the contract is centralized and the views stay thin. Server components fetch where possible;
the predictor form is a small client component.

## Complexity Tracking

> No constitution violations — nothing to justify.
