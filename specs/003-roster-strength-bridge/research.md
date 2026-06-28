# Phase 0 Research: ENC Roster-Strength Bridge (Phase 3)

Decisions resolving the technical unknowns. Each records the decision, why, and rejected
alternatives.

## R1. Player-side attribution — offline, from cached HTML + match identity

**Decision**: Populate the existing-but-null `player_map_stat.team_id` (which side each
player was on) by matching the parser's per-player `team_abbrev` to the match's two teams
(`team_a_id`/`team_b_id`, with names/abbreviations) recorded by feature 002. This is an
**offline re-parse** of cached HTML (no scraping). Where the abbreviation is ambiguous or the
match is unlabeled, the stat is left unattributed (excluded, logged).

**Rationale**: Player-level signal (R2) needs to know who won; attribution is the missing
link and is derivable offline with provenance (Constitution I). Reuses data already captured.

**Alternatives**: Store team per stat at collection time (would require re-collecting); infer
side from co-occurrence clustering (fragile). Offline abbreviation match is simplest + exact.

## R2. Player rating — chronological player Elo + recent form (leakage-free)

**Decision**: Compute a per-**player** Elo by replaying all attributed matches in time order:
in each match, every player on the winning side gains, the losing side loses (shared team
result), updating that player's rating. Also track each player's recent win-rate (form) and
match volume. A player's strength **as of** a date uses only matches before it.

**Rationale**: Player Elo is opponent-adjusted and moves a player's rating by who they beat,
independent of which club entity they currently represent — exactly what's needed to value a
national-team roster. Leakage-freedom is structural (replay updates only after emitting
as-of state), mirroring feature 002 (R2/R3).

**Alternatives**: Player average VLR rating (self-normalized ~1.0, weak discrimination, no
opponent adjustment); per-club Elo only (can't transfer to a national roster). Player Elo
chosen; average rating kept as a *baseline* (R5).

## R3. Roster aggregation — lineup mean with sparse-aware confidence

**Decision**: A team's strength **as of** a date = an aggregate (mean, optionally top-k) of
its lineup's player Elos, plus aggregate form and total volume. For a national team the
lineup is its **active roster**; for a club match it is the players who actually played.
Players below a minimum-history threshold contribute a transparent prior and lower the team's
confidence; if too much of a roster is sparse, the team is flagged low-confidence.

**Rationale**: Implements FR-001/FR-003 — a defensible, explainable team strength that
degrades gracefully and never invents certainty (SC-003/SC-007 lineage).

**Alternatives**: Single best player (ignores depth); sum (rewards roster size). Mean (with
optional top-k) is the transparent middle.

## R4. Matchup model — roster-strength diff → calibrated probability, learned on club matches

**Decision**: Encode a matchup as the **difference** of the two teams' roster-derived
strengths (Elo diff, form diff, log-volume diff) and map it to a win probability with a
calibrated logistic regression — reusing feature-002's model/calibration/metrics. **Train and
evaluate on real club matches with known lineups** (each side's strength computed from its
actual lineup, as-of before the match), then apply the same function to ENC rosters.

**Rationale**: Club matches are the only place real outcomes exist, so the bridge's value is
earned there (Constitution IV); applying the identical function to ENC rosters is then a pure
substitution. Reusing 002 keeps the stack small and the probabilities calibrated.

**Alternatives**: Reuse the 002 club-Elo model directly with a substituted team Elo (scales
differ between team Elo and roster-mean player Elo → miscalibrated); a bespoke model (more
code). A dedicated calibrated model on roster-strength diffs is the clean fit.

## R5. Baselines — explicit, non-derived, on identical matches

**Decision**: Compare the bridge against at least: (a) **roster-tier pedigree** (feature-001
`roster-tier-seed`) and (b) a **naive player-rating average** (mean of the lineup's average
VLR rating, no opponent adjustment). Both produce a probability/ordering on the same held-out
matches; a bridge that does not beat them is reported as such (FR-005/FR-006).

**Rationale**: A derived strength is only credible beating an explicit, simpler rule
(Constitution IV). Both baselines are cheap and reuse existing data.

## R6. ENC application + locked artifacts

**Decision**: Apply the bridge to the 16 ENC rosters as of the lock date to produce (a)
confident `enc-predict` matchups and (b) a roster-derived 16-team `enc-ranking`, written as a
**new** dated, immutable artifact under `artifacts/models/bridge/` (never modifying 001/002
artifacts). Each carries the run id, feature/config fingerprint, and contributing players for
traceability (FR-007/FR-010, Constitution II).

**Rationale**: Closes the loop the spec asks for — confident ENC outputs — while honoring
immutability and traceability.

## Open items (data, validated at runtime)

- Attribution coverage: the share of `player_map_stat` rows whose side resolves cleanly from
  the abbreviation (ambiguous ones are excluded, logged — never guessed).
- Whether mean or top-k roster aggregation evaluates better on club matches (chosen by the
  honest evaluation, not assumed).
