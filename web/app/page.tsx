import { ProvenanceLine } from "@/components/Provenance";
import { Empty } from "@/components/States";
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
        <Head />
        {err.status === 404 ? (
          <Empty kicker="No edition yet" title="The ranking hasn’t gone to press.">
            Publish one with <code>vctm enc-ranking</code>, then reload.
          </Empty>
        ) : (
          <Empty kicker="Off the wire" title="The ledger is unavailable.">
            {err.message}
          </Empty>
        )}
      </>
    );
  }

  const scores = ranking.teams.map((t) => t.score);
  const lo = Math.min(...scores);
  const hi = Math.max(...scores);
  const width = (s: number) => 0.16 + 0.84 * ((s - lo) / (hi - lo || 1));

  return (
    <>
      <Head />
      <ol className="ledger">
        {ranking.teams.map((t, i) => (
          <li
            key={t.position}
            className={`entry${t.position === 1 ? " lead" : ""}`}
            style={{ animationDelay: `${0.05 + i * 0.035}s` }}
          >
            <span className="rank">{t.position}</span>
            <div className="team-block">
              <div className="team">{t.team}</div>
              <div className="meter">
                <span style={{ "--w": width(t.score) } as React.CSSProperties} />
              </div>
            </div>
            <div className="figure">
              <span className="score">{Math.round(t.score)}</span>
              <span className={`conf ${t.confidence}`}>{t.confidence}</span>
            </div>
          </li>
        ))}
      </ol>
      <ProvenanceLine p={ranking.provenance} />
    </>
  );
}

function Head() {
  return (
    <div className="section-head">
      <div>
        <p className="kicker">Power Ranking · ENC 2026</p>
        <h1 className="headline">The sixteen, in order.</h1>
      </div>
      <p className="standfirst">
        Strength is each squad’s roster rated by its players’ recent club form — opponent-
        adjusted, leakage-free. The bar is the spread; the number is the rating.
      </p>
    </div>
  );
}
