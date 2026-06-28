---
description: "Task list for ENC Web Demo (Phase 5)"
---

# Tasks: ENC Web Demo (Phase 5)

**Input**: Design documents from `specs/005-web-demo/`. A Next.js frontend in `web/`.

**Gate**: Constitution III adapted for a frontend — the headless gate is a green production
build + type check (`npm run build`, `tsc --noEmit`); visual/interaction QA is a human step.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Scaffold the Next.js App-Router project in web/ (package.json, tsconfig.json,
  next.config.mjs, .env.example, .gitignore)
- [X] T002 [P] Typed API client (ranking/predict/evaluation + base URL + ApiError) in web/lib/api.ts

## Phase 2: Foundational

- [X] T003 Root layout + nav + global styles (web/app/layout.tsx, web/app/globals.css)
- [X] T004 [P] Shared components: Badge, ProvenanceLine, Unavailable state in web/components/

## Phase 3: US1 — Ranking (P1, MVP)

- [X] T005 [US1] Home page renders the 16-team ranking + confidence + provenance, with a clear
  "unavailable/not published" state in web/app/page.tsx

## Phase 4: US2 — Predict (P1)

- [X] T006 [US2] Matchup predictor (team selects + date → probabilities, winner, contributors,
  low-confidence note, error state) in web/app/predict/page.tsx

## Phase 5: US3 — Honesty (P2)

- [X] T007 [US3] Evaluation view: model vs. baseline metrics + verdict + provenance in
  web/app/honesty/page.tsx

## Phase 6: Polish

- [X] T008 [P] web/README.md run/gates docs
- [X] T009 Headless gate green: `npm run typecheck` + `npm run build` succeed; SSR verified to
  render real data against a running API

---

## Notes

- The site adds no business logic — it only reads and renders the feature-004 API, preserving
  confidence flags and "model vs. baseline" framing.
- Graceful states for API down / 404 / prediction errors (no blank crash).
- Visual/interaction QA is performed by a human in a browser (the build + type check + SSR
  smoke are the automated gates here).
