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

  const bLeads = result ? result.p_b > result.p_a : false;

  return (
    <>
      <div className="section-head">
        <div>
          <p className="kicker">Head&#8209;to&#8209;Head</p>
          <h1 className="headline">Run the tape.</h1>
        </div>
        <p className="standfirst">
          Two nations, one date. The forecast reads only what was known before that day —
          each roster’s club form, nothing from the future.
        </p>
      </div>

      <form onSubmit={onSubmit}>
        <div className="field" style={{ maxWidth: 220, marginTop: 24 }}>
          <label htmlFor="asof">Forecast as of</label>
          <input
            id="asof"
            type="date"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
          />
        </div>
        <div className="matchup-form">
          <div className="field">
            <label htmlFor="a">Home</label>
            <select id="a" value={teamA} onChange={(e) => setTeamA(e.target.value)}>
              {teams.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
          <span className="vs">vs</span>
          <div className="field">
            <label htmlFor="b">Away</label>
            <select id="b" value={teamB} onChange={(e) => setTeamB(e.target.value)}>
              {teams.map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
          <button
            className="cast"
            type="submit"
            disabled={loading || !teamA || !teamB || teamA === teamB}
          >
            {loading ? "Calling…" : "Call it"}
          </button>
        </div>
      </form>

      {error ? (
        <div className="empty" style={{ marginTop: 8 }}>
          <p className="kicker">No call</p>
          <h2 style={{ fontSize: "var(--step-1)" }}>{error}</h2>
        </div>
      ) : null}

      {result ? (
        <section className="verdict-split">
          <div className="split-names">
            <span className="a">{result.team_a}</span>
            <span className="b">{result.team_b}</span>
          </div>
          <div className={`split-bar${bLeads ? " b-leads" : ""}`}>
            <div className="a" style={{ flexBasis: `${result.p_a * 100}%` }}>
              {(result.p_a * 100).toFixed(0)}%
            </div>
            <div className="b" style={{ flexBasis: `${result.p_b * 100}%` }}>
              {(result.p_b * 100).toFixed(0)}%
            </div>
          </div>
          <div className="rosters">
            <div className="a">
              <strong>Carrying {result.team_a}</strong>
              {result.contributors_a.join(" · ") || "—"}
            </div>
            <div className="b">
              <strong>Carrying {result.team_b}</strong>
              {result.contributors_b.join(" · ") || "—"}
            </div>
          </div>
          <p className="called">
            The call: <b>{result.winner}</b>.
          </p>
          {result.low_confidence ? (
            <p className="footnote">
              Soft read — at least one roster has thin club history, so don’t bet the house.
            </p>
          ) : null}
          <ProvenanceLine p={result.provenance} />
        </section>
      ) : null}
    </>
  );
}
