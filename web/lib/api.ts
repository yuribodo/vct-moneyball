// Typed client for the feature-004 read-only prediction API.
// The only place the web app knows the API shape — views stay thin (FR-006).

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:8000";

export type Provenance = {
  source: string;
  version?: string | null;
  run_id?: string | null;
  as_of?: string | null;
  data_window?: Record<string, string> | null;
  feature_fingerprint?: string | null;
};

export type RankingTeam = {
  position: number;
  team: string;
  score: number;
  confidence: string;
  elo_margin_to_next?: number | null;
  separation?: string | null;
};
export type Ranking = {
  version: string;
  as_of?: string | null;
  aggregation?: string | null;
  teams: RankingTeam[];
  provenance: Provenance;
};

export type Prediction = {
  team_a: string;
  team_b: string;
  as_of: string;
  p_a: number;
  p_b: number;
  winner: string;
  low_confidence: boolean;
  elo_a: number;
  elo_b: number;
  contributors_a: string[];
  contributors_b: string[];
  provenance: Provenance;
};

export type TeamContributor = {
  player: string;
  player_score: number;
  maps_played: number;
  confidence: string;
  low_history_baseline: boolean;
};
export type TeamMapScore = { map: string; map_score: number; confidence: string };
export type TeamDetail = {
  team: string;
  country: string | null;
  position: number;
  team_score: number;
  roster_elo: number | null;
  confidence: string;
  contributors: TeamContributor[];
  map_breakdown: TeamMapScore[];
  provenance: Provenance;
};

export type MatrixTeam = {
  team: string;
  position: number;
  elo: number;
  confidence: string;
  contributors: string[];
  country: string | null;
};
export type Matrix = {
  as_of: string;
  aggregation: string;
  teams: MatrixTeam[];
  p: number[][];
  provenance: Provenance;
};

export type Metrics = {
  log_loss: number;
  accuracy: number;
  brier: number;
  calibration_error?: number | null;
};
export type Evaluation = {
  kind: string;
  cutoff: string;
  n_train: number;
  n_eval: number;
  leakage_verified: boolean;
  model_metrics: Metrics;
  baselines: { label: string; metrics: Metrics }[];
  provenance: Provenance;
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { cache: "no-store" });
  } catch {
    throw new ApiError(0, `API unreachable at ${BASE} — is \`vctm serve\` running?`);
  }
  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as { error?: string };
      if (body.error) message = body.error;
    } catch {
      /* keep statusText */
    }
    throw new ApiError(res.status, message);
  }
  return (await res.json()) as T;
}

export const api = {
  base: BASE,
  ranking: (source = "roster") => get<Ranking>(`/enc/ranking?source=${source}`),
  predict: (teamA: string, teamB: string, asOf?: string) =>
    get<Prediction>(
      `/enc/predict?team_a=${encodeURIComponent(teamA)}&team_b=${encodeURIComponent(teamB)}` +
        (asOf ? `&as_of=${encodeURIComponent(asOf)}` : ""),
    ),
  evaluation: (kind = "bridge") => get<Evaluation>(`/enc/evaluation?kind=${kind}`),
  team: (name: string, version?: string) =>
    get<TeamDetail>(
      `/enc/team/${encodeURIComponent(name)}` + (version ? `?version=${version}` : ""),
    ),
  matrix: (asOf?: string, aggregation = "mean") =>
    get<Matrix>(
      `/enc/matrix?aggregation=${aggregation}` + (asOf ? `&as_of=${encodeURIComponent(asOf)}` : ""),
    ),
};
