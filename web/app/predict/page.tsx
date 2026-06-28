"use client";

import { useEffect, useState } from "react";
import { ProvenanceLine } from "@/components/Provenance";
import { api, ApiError, type Prediction } from "@/lib/api";

export default function PredictPage() {
  const [teams, setTeams] = useState<string[]>([]);
  const [teamA, setTeamA] = useState("");
  const [teamB, setTeamB] = useState("");
  const [asOf, setAsOf] = useState("2026-11-08");
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .ranking()
      .then((r) => {
        const names = r.teams.map((t) => t.team);
        setTeams(names);
        setTeamA(names[0] ?? "");
        setTeamB(names[1] ?? "");
      })
      .catch((e: ApiError) => setError(e.message));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.predict(teamA, teamB, asOf));
    } catch (err) {
      setError((err as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1>Predict a matchup</h1>
      <p className="lede">
        Pick two ENC teams and a date. The win probability comes from each roster&apos;s club
        form, using only data from before that date.
      </p>

      <form className="matchup" onSubmit={onSubmit}>
        <div>
          <label htmlFor="a">Team A</label>
          <select id="a" value={teamA} onChange={(e) => setTeamA(e.target.value)}>
            {teams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="b">Team B</label>
          <select id="b" value={teamB} onChange={(e) => setTeamB(e.target.value)}>
            {teams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" disabled={loading || !teamA || !teamB || teamA === teamB}>
          {loading ? "…" : "Predict"}
        </button>
      </form>

      {error ? (
        <div className="state">
          <strong>Could not predict</strong>
          <div style={{ marginTop: 6 }}>{error}</div>
        </div>
      ) : null}

      {result ? (
        <>
          <div className="matchup-result">
            <TeamCard
              name={result.team_a}
              prob={result.p_a}
              contributors={result.contributors_a}
              win={result.winner === result.team_a}
            />
            <TeamCard
              name={result.team_b}
              prob={result.p_b}
              contributors={result.contributors_b}
              win={result.winner === result.team_b}
            />
          </div>
          {result.low_confidence ? (
            <div className="note">
              Low confidence — at least one roster has sparse club history, so this is a soft
              read, not a strong call.
            </div>
          ) : null}
          <ProvenanceLine p={result.provenance} />
        </>
      ) : null}
    </>
  );
}

function TeamCard({
  name,
  prob,
  contributors,
  win,
}: {
  name: string;
  prob: number;
  contributors: string[];
  win: boolean;
}) {
  return (
    <div className={`team-card${win ? " win" : ""}`}>
      <div className="team-name">{name}</div>
      <div className="prob">{(prob * 100).toFixed(1)}%</div>
      <div className="bar">
        <span style={{ width: `${prob * 100}%` }} />
      </div>
      <div className="contribs">Top: {contributors.join(", ") || "—"}</div>
    </div>
  );
}
