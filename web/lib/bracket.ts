// Pure, matrix-driven single-elimination bracket simulation.
// No network: feed it a Matrix (16 teams seeded by position + pairwise probabilities).

import type { Matrix } from "@/lib/api";

// Standard 16-team seed order so the top seeds meet as late as possible.
const SEED_ORDER = [1, 16, 8, 9, 5, 12, 4, 13, 3, 14, 6, 11, 7, 10, 2, 15];

export type BracketMatch = {
  /** indices into Matrix.teams */
  a: number;
  b: number;
  /** P(a beats b) */
  pA: number;
  /** index of the winner */
  winner: number;
};

export type Round = {
  name: string;
  matches: BracketMatch[];
};

export type BracketResult = {
  rounds: Round[];
  champion: number;
};

const ROUND_NAMES = ["Round of 16", "Quarterfinals", "Semifinals", "Final"];

type Mode = "deterministic" | "probabilistic";

function pick(m: Matrix, a: number, b: number, mode: Mode, rand: () => number): BracketMatch {
  const pA = m.p[a][b];
  let winner: number;
  if (mode === "probabilistic") {
    winner = rand() < pA ? a : b;
  } else {
    winner = pA >= 0.5 ? a : b;
  }
  return { a, b, pA, winner };
}

/** Map team array index by seed (position). teams are NOT guaranteed sorted. */
function bySeed(m: Matrix): number[] {
  const idxByPos = new Map<number, number>();
  m.teams.forEach((t, i) => idxByPos.set(t.position, i));
  return SEED_ORDER.map((seed) => idxByPos.get(seed) ?? 0);
}

export function simulateBracket(
  m: Matrix,
  mode: Mode = "deterministic",
  rand: () => number = Math.random,
): BracketResult {
  let current = bySeed(m); // 16 team indices in bracket order
  const rounds: Round[] = [];

  for (let r = 0; r < ROUND_NAMES.length; r++) {
    const matches: BracketMatch[] = [];
    const next: number[] = [];
    for (let i = 0; i < current.length; i += 2) {
      const match = pick(m, current[i], current[i + 1], mode, rand);
      matches.push(match);
      next.push(match.winner);
    }
    rounds.push({ name: ROUND_NAMES[r], matches });
    current = next;
  }

  return { rounds, champion: current[0] };
}

/** Monte Carlo: probability each team wins the title over N probabilistic runs. */
export function titleOdds(m: Matrix, runs = 2000): { index: number; odds: number }[] {
  const wins = new Array(m.teams.length).fill(0);
  for (let i = 0; i < runs; i++) {
    const { champion } = simulateBracket(m, "probabilistic");
    wins[champion]++;
  }
  return m.teams
    .map((_, index) => ({ index, odds: wins[index] / runs }))
    .sort((a, b) => b.odds - a.odds);
}
