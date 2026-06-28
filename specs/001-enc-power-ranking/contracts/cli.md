# CLI Contract: `vctm` (ENC 2026 Power Ranking MVP)

The MVP exposes its pipeline through a single CLI, `vctm`. Each command is a pipeline
stage; all are deterministic given versioned inputs + config. Text in/out, JSON
optional; errors to stderr with non-zero exit (Const. CLI/observability discipline).

## `vctm collect`

Collect ENC teams, rosters, and in-window matches from VLR.gg into Postgres, caching
raw HTML.

- **Options**: `--window-months <int>` (default from config), `--cutoff <date>`,
  `--use-cache/--no-cache` (default `--use-cache`), `--rate-limit <req/min>`.
- **Preconditions**: Postgres reachable; migrations applied.
- **Postconditions**: `team`/`player`/`team_player`/`match`/`match_map`/
  `player_map_stat` upserted with `source_url` + `captured_at`; raw HTML in the cache.
- **Exit/validation**: non-zero if the source is unreachable and no cache exists, or if
  fewer/more than 16 ENC teams are resolved.
- **Output**: summary counts (teams, players, matches, stat rows) as text or `--json`.

## `vctm build-ranking`

Score players per map, aggregate to teams, and write a dated, immutable ranking
artifact (JSON + Markdown) and the corresponding `ranking*` DB rows.

- **Options**: `--version <id>` (e.g. `enc-2026.v1`), `--published-at <timestamptz>`
  (default now), `--tournament-start <timestamptz>` (lock deadline),
  `--out-dir <path>` (default `artifacts/rankings/enc-2026/`),
  `--supersedes <version>` (optional).
- **Preconditions**: exactly 16 ENC teams each with ≥1 active roster player; full map
  pool present; all referenced rows carry provenance.
- **Postconditions**: artifact directory `…/<published-at>/` written with
  `ranking.json` (validates against `ranking-artifact.schema.json`) + `ranking.md`;
  `ranking`, `ranking_entry`, `ranking_map_breakdown` rows inserted (append-only).
- **Exit/validation**: non-zero (and writes nothing) if `published_at >=
  tournament-start`, if teams ≠ 16, if any in-pool map is missing for any team, or if
  the target artifact directory already exists (never overwrite — Const. II).
- **Output**: artifact path + the 16-team ordered table.

## `vctm evaluate`

After the tournament, compare a locked ranking against final standings.

- **Options**: `--version <id>` (which locked ranking), `--standings <path>` (final
  results input), `--baseline <label>` (e.g. `vlr-seed`), `--metric <name>...`
  (default `spearman_rho`, `kendall_tau`, `top4_hit_rate`).
- **Preconditions**: the named `ranking` exists and is frozen; standings provided.
- **Postconditions**: `outcome_comparison` rows written; a comparison report emitted.
  The referenced ranking is read-only.
- **Exit/validation**: non-zero if the ranking version is unknown or standings are
  malformed.
- **Output**: per-metric predicted vs baseline values (text or `--json`).

## Cross-cutting

- `--json` on every command for machine-readable output.
- Non-zero exit on any validation failure; human-readable reason on stderr.
- No command mutates a previously published artifact or `ranking*` row.
