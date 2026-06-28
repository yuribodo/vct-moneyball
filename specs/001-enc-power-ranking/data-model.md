# Phase 1 Data Model: ENC 2026 Power Ranking (MVP)

Postgres 16 schema (system of record). Conventions: surrogate `bigint` PKs
(`GENERATED ALWAYS AS IDENTITY`), `text` for strings, `timestamptz` for time,
`numeric` for stats (never float for stored metrics), natural keys enforced with
`UNIQUE` constraints, foreign keys with explicit `ON DELETE`, and indexes on every FK
and on the columns the pipeline filters/joins by. Provenance columns
(`source_url text`, `captured_at timestamptz`) live on every collected (non-derived)
row (Constitution I).

## Entity overview

```text
team 1───* team_player *───1 player
map  1───* match_map
match 1──* match_map 1──* player_map_stat *──1 player
player_map_stat *──1 team
ranking 1─* ranking_entry *─1 team
ranking 1─* ranking_map_breakdown *─1 team, *─1 map
ranking 1─? outcome_comparison
```

## Collected entities (carry provenance)

### `team`
- `id` PK
- `name text NOT NULL`
- `country text NOT NULL` — national team identity (ENC)
- `vlr_team_id text` — VLR.gg identifier, `UNIQUE` when present
- `is_enc_2026 boolean NOT NULL DEFAULT false` — in the MVP cohort
- `source_url text NOT NULL`, `captured_at timestamptz NOT NULL`
- **Constraints**: `UNIQUE (name, country)`
- **Validation**: exactly 16 rows with `is_enc_2026 = true` before a ranking builds.

### `player`
- `id` PK
- `handle text NOT NULL`
- `vlr_player_id text` — `UNIQUE` when present
- `source_url text NOT NULL`, `captured_at timestamptz NOT NULL`
- **Constraints**: `UNIQUE (vlr_player_id)`; `UNIQUE (handle)` only if no VLR id.

### `team_player` (roster membership at lock time)
- `id` PK
- `team_id` FK → `team(id)` `ON DELETE CASCADE`
- `player_id` FK → `player(id)` `ON DELETE CASCADE`
- `role text NULL` — for the cohort/role baseline (R3)
- `is_active boolean NOT NULL DEFAULT true`
- `source_url text NOT NULL`, `captured_at timestamptz NOT NULL`
- **Constraints**: `UNIQUE (team_id, player_id)`
- **Index**: `(player_id)`

### `map`
- `id` PK
- `name text NOT NULL UNIQUE`
- `in_pool boolean NOT NULL DEFAULT true` — current competitive pool
- `source_url text NULL`, `captured_at timestamptz NULL`

### `match`
- `id` PK
- `vlr_match_id text NOT NULL UNIQUE`
- `event text NOT NULL`
- `played_at timestamptz NOT NULL` — used for the data-window filter
- `source_url text NOT NULL`, `captured_at timestamptz NOT NULL`
- **Index**: `(played_at)`, `(event)`

### `match_map` (a single map played within a match)
- `id` PK
- `match_id` FK → `match(id)` `ON DELETE CASCADE`
- `map_id` FK → `map(id)` `ON DELETE RESTRICT`
- `winner_team_id` FK → `team(id)` `ON DELETE SET NULL` (nullable)
- **Constraints**: `UNIQUE (match_id, map_id)` (per match a map appears once)
- **Index**: `(map_id)`, `(match_id)`

### `player_map_stat` (per player, per map played — the scoring evidence)
- `id` PK
- `match_map_id` FK → `match_map(id)` `ON DELETE CASCADE`
- `player_id` FK → `player(id)` `ON DELETE CASCADE`
- `team_id` FK → `team(id)` `ON DELETE SET NULL`
- `rating numeric(5,2) NULL`, `acs numeric(6,1) NULL`, `kast numeric(5,2) NULL`,
  `adr numeric(6,1) NULL`, `kills int NULL`, `deaths int NULL`, `assists int NULL`
- `source_url text NOT NULL`, `captured_at timestamptz NOT NULL`
- **Constraints**: `UNIQUE (match_map_id, player_id)`
- **Index**: `(player_id)`, `(team_id)`, `(match_map_id)`

## Derived / output entities (no external provenance; lineage = the inputs + config)

### `ranking` (the locked, dated artifact header)
- `id` PK
- `published_at timestamptz NOT NULL` — lock timestamp (must precede tournament start)
- `tournament_start timestamptz NOT NULL` — recorded lock deadline (first ENC match);
  persisted for provenance so the deadline is part of the locked record
- `version text NOT NULL` — e.g. `enc-2026.v1`
- `data_window_start timestamptz NOT NULL`, `data_window_end timestamptz NOT NULL`
- `config_hash text NOT NULL` — hash of scoring params (weights, threshold) for lineage
- `supersedes_ranking_id` FK → `ranking(id)` `ON DELETE RESTRICT` (nullable)
- `notes text NULL`
- **Constraints**: `UNIQUE (version)`; rows are **append-only** (no UPDATE/DELETE by process).

### `ranking_entry` (one team's place in a ranking)
- `id` PK
- `ranking_id` FK → `ranking(id)` `ON DELETE CASCADE`
- `team_id` FK → `team(id)` `ON DELETE RESTRICT`
- `position int NOT NULL` — strict 1..16
- `team_score numeric(8,4) NOT NULL`
- `confidence text NOT NULL` — e.g. `high|medium|low` (R3)
- **Constraints**: `UNIQUE (ranking_id, team_id)`, `UNIQUE (ranking_id, position)`,
  `CHECK (position BETWEEN 1 AND 16)`

### `ranking_map_breakdown` (a team's strength on one map within a ranking)
- `id` PK
- `ranking_id` FK → `ranking(id)` `ON DELETE CASCADE`
- `team_id` FK → `team(id)` `ON DELETE RESTRICT`
- `map_id` FK → `map(id)` `ON DELETE RESTRICT`
- `map_score numeric(8,4) NOT NULL`
- `confidence text NOT NULL`
- **Constraints**: `UNIQUE (ranking_id, team_id, map_id)`

### `outcome_comparison` (post-tournament evaluation — US3)
- `id` PK
- `ranking_id` FK → `ranking(id)` `ON DELETE CASCADE`
- `evaluated_at timestamptz NOT NULL`
- `metric text NOT NULL` — e.g. `spearman_rho`, `kendall_tau`, `top4_hit_rate`
- `predicted_value numeric NOT NULL`
- `baseline_label text NOT NULL`, `baseline_value numeric NOT NULL`
- `final_standings_source text NOT NULL`
- **Constraints**: `UNIQUE (ranking_id, metric, baseline_label)`

## Validation rules (enforced in code, derived from spec)

- A `ranking` can be built only when exactly 16 `team` rows have `is_enc_2026 = true`
  and every such team has at least one active `team_player` (FR-001, SC-001).
- `ranking_map_breakdown` MUST cover every `map` with `in_pool = true` for every team
  (FR-004, SC-002).
- `ranking.published_at` MUST be at least 1 full day (24h) before
  `ranking.tournament_start` (FR-007, SC-003).
- A player below the min-history threshold contributes via the labeled baseline and
  sets the relevant `confidence` to `low` (FR-010/FR-012, SC-007).
- Every `player_map_stat`/`match`/`team`/`player` row used by a ranking has non-null
  `source_url` + `captured_at` (FR-009, SC-004).

## State / lifecycle

- Collected rows: inserted/upserted by the collect stage; corrections re-run collection
  (no manual edits — Const. I).
- `ranking*` rows: written once by the rank stage, then immutable. A revision creates a
  new `ranking` with `supersedes_ranking_id` set (Const. II).
- `outcome_comparison`: written once after the tournament, references a frozen ranking.
