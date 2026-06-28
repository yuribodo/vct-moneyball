import { ProvenanceLine } from "@/components/Provenance";
import { Empty } from "@/components/States";
import { api, ApiError, type Metrics } from "@/lib/api";

export const dynamic = "force-dynamic";

const ll = (m: Metrics) => m.log_loss.toFixed(4);
const acc = (m: Metrics) => (m.accuracy * 100).toFixed(1) + "%";
const brier = (m: Metrics) => m.brier.toFixed(4);

export default async function Honesty() {
  let ev;
  try {
    ev = await api.evaluation("bridge");
  } catch (e) {
    const err = e as ApiError;
    return (
      <>
        <Head />
        {err.status === 404 ? (
          <Empty kicker="Not yet settled" title="No reckoning on record.">
            Run <code>vctm eval-bridge</code>, then reload.
          </Empty>
        ) : (
          <Empty kicker="Off the wire" title="The reckoning is unavailable.">
            {err.message}
          </Empty>
        )}
      </>
    );
  }

  const best = ev.baselines.reduce((a, b) =>
    a.metrics.log_loss <= b.metrics.log_loss ? a : b,
  );
  const beats = ev.model_metrics.log_loss < best.metrics.log_loss;

  return (
    <>
      <Head />
      <p className="verdict-line">
        On data it never saw, the model{" "}
        {beats ? (
          <span className="beats">beats</span>
        ) : (
          <span style={{ color: "var(--ink-2)", fontStyle: "italic" }}>does not beat</span>
        )}{" "}
        its baseline.
      </p>

      <table className="scoreboard">
        <thead>
          <tr>
            <th>Predictor</th>
            <th>Log-loss</th>
            <th>Accuracy</th>
            <th>Brier</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="who">the model</td>
            <td>{ll(ev.model_metrics)}</td>
            <td>{acc(ev.model_metrics)}</td>
            <td>{brier(ev.model_metrics)}</td>
          </tr>
          {ev.baselines.map((b) => (
            <tr key={b.label}>
              <td className="who" style={{ color: "var(--ink-2)" }}>
                {b.label}
              </td>
              <td>{ll(b.metrics)}</td>
              <td>{acc(b.metrics)}</td>
              <td>{brier(b.metrics)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <dl className="terms">
        <div className="term">
          <dt>Held-out matches</dt>
          <dd>{ev.n_eval.toLocaleString()}</dd>
        </div>
        <div className="term">
          <dt>Trained on</dt>
          <dd>{ev.n_train.toLocaleString()}</dd>
        </div>
        <div className="term">
          <dt>No leakage</dt>
          <dd>{ev.leakage_verified ? "Verified" : "—"}</dd>
        </div>
        <div className="term">
          <dt>Cutoff</dt>
          <dd>{ev.cutoff.slice(0, 10)}</dd>
        </div>
      </dl>

      <ProvenanceLine p={ev.provenance} />
    </>
  );
}

function Head() {
  return (
    <div className="section-head">
      <div>
        <p className="kicker">The Reckoning</p>
        <h1 className="headline">Was it right?</h1>
      </div>
      <p className="standfirst">
        A claim is only worth what it earns on matches it never trained on, against an honest
        baseline. Lose to the baseline and we say so.
      </p>
    </div>
  );
}
