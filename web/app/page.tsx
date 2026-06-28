import { Badge } from "@/components/Badge";
import { ProvenanceLine } from "@/components/Provenance";
import { Unavailable } from "@/components/States";
import { api, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Home() {
  let ranking;
  try {
    ranking = await api.ranking();
  } catch (e) {
    const err = e as ApiError;
    return (
      <>
        <h1>ENC 2026 Power Ranking</h1>
        <Unavailable
          title={err.status === 404 ? "No ranking published yet" : "Ranking unavailable"}
          detail={
            err.status === 404
              ? "Publish one with `vctm enc-ranking`, then reload."
              : err.message
          }
        />
      </>
    );
  }

  return (
    <>
      <h1>ENC 2026 Power Ranking</h1>
      <p className="lede">
        The 16 national teams ranked by roster-derived strength — each player&apos;s recent
        club form, aggregated. Locked and dated before kickoff.
      </p>
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th className="pos">#</th>
              <th>Team</th>
              <th className="num">Strength</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {ranking.teams.map((t) => (
              <tr key={t.position} className={`rank-${t.position}`}>
                <td className="pos">{t.position}</td>
                <td>{t.team}</td>
                <td className="num">{Math.round(t.score)}</td>
                <td>
                  <Badge confidence={t.confidence} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ProvenanceLine p={ranking.provenance} />
    </>
  );
}
