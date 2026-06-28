# Phase 0 Research: ENC Prediction API (Phase 4)

Decisions resolving the technical unknowns. Each records the decision, why, and rejected
alternatives.

## R1. Framework — FastAPI + Uvicorn

**Decision**: Build the service with **FastAPI** (already declared in the `api` group), served
by Uvicorn. Pydantic models define the response schemas and auto-generate OpenAPI docs.

**Rationale**: It is the constitution's designated serving stack, gives typed,
self-documenting responses, and tests fully headless via `TestClient` (no running server).

**Alternatives**: Flask (less typing/async, manual schema); a bare ASGI app (reinvents
routing/validation). FastAPI is the fit.

## R2. Rankings/evaluations — serve the published artifact, read-only

**Decision**: The ranking and evaluation endpoints **read the latest committed artifact** from
`artifacts/` (the feature-003 roster ranking / the eval reports) and return it with its
version/run id — never recomputing or mutating it. "Latest" = most recent by published
date/version; a specific version is retrievable by id.

**Rationale**: Honors Constitution II (locked artifacts served byte-faithfully) and keeps the
endpoint trivial and fast (file read). Provenance comes for free (the artifact carries it).

**Alternatives**: Recompute rankings on request (risks drifting from the locked artifact);
serve from the DB `ranking*` rows (the committed file is the canonical locked record). Rejected.

## R3. Live predictions — delegate to the feature-003 bridge

**Decision**: `GET /enc/predict` calls the **same `enc-predict` logic** (bridge: train inline,
roster strength as-of, calibrated probability) used by the CLI, returning probabilities,
winner, confidence, and top contributors. The endpoint is a thin transport over
`bridge.model` + `bridge.features`.

**Rationale**: Guarantees CLI-parity (FR-005) by construction — one code path. Deterministic
and fast (<1s).

**Alternatives**: Precompute all 16×16 matchups (stale, inflexible); a separate API-side model
(would drift from the CLI). Rejected.

## R4. Testing — FastAPI TestClient, headless + CLI parity

**Decision**: Test with FastAPI's `TestClient` (httpx) against the isolated `<db>_test`:
endpoint status/shape, low-confidence flagging, error/unavailable cases, and a **parity test**
asserting the predict endpoint equals the CLI handler for the same inputs.

**Rationale**: Headless, deterministic, and proves SC-002/SC-005. httpx is added to the `api`
group for the client.

**Alternatives**: Spinning a live Uvicorn in tests (slower, flaky). TestClient is standard.

## R5. Error model — clear client vs. server vs. not-found

**Decision**: Map failures to honest HTTP statuses: unknown team / malformed input → **400**;
missing artifact / no data → **404**; database unreachable → **503**; never a 200 with empty
or misleading data, never an unhandled 500. A consistent JSON error body carries a message.

**Rationale**: Implements FR-007/SC-005 — a consumer can always tell what happened.

**Alternatives**: Always-200 with an error field (hides failures); leaking stack traces.
Rejected.

## R6. Provenance in every response

**Decision**: Every ranking/prediction/evaluation response includes a provenance block — the
source artifact version (or model run id) + data window/feature fingerprint where applicable —
so a consumer can audit any served value (FR-008/SC-004).

**Rationale**: The project's credibility is traceability; the API must not strip it.

## Open items (validated at runtime)

- Which published ranking is "current" by default (the roster-derived feature-003 artifact),
  with the feature-001 locked ranking also retrievable by version.
- Whether `vctm serve` (a CLI subcommand) or a documented `uvicorn` command is the run entry —
  both call the same app factory; decided in implementation for ergonomics.
