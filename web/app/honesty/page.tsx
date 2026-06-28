import { ProvenanceLine } from "@/components/Provenance";
import { Unavailable } from "@/components/States";
import { api, ApiError, type Metrics } from "@/lib/api";

export const dynamic = "force-dynamic";

function fmt(m: Metrics) {
  return {
    ll: m.log_loss.toFixed(4),
    acc: (m.accuracy * 100).toFixed(1) + "%",
    brier: m.brier.toFixed(4),
  };
}

export default async function Honesty() {
  let evaluation;
  try {
    evaluation = await api.evaluation("bridge");
  } catch (e) {
    const err = e as ApiError;
    return (
      <>
        <h1>Who was right?</h1>
        <Unavailable
          title={err.status === 404 ? "No evaluation published yet" : "Evaluation unavailable"}
          detail={
            err.status === 404 ? "Run `vctm eval-bridge`, then reload." : err.message
          }
        />
      </>
    );
  }

  const best = evaluation.baselines.reduce((a, b) =>
    a.metrics.log_loss <= b.metrics.log_loss ? a : b,
  );
  const beats = evaluation.model_metrics.log_loss < best.metrics.log_loss;
  const model = fmt(evaluation.model_metrics);

  return (
    <>
      <h1>Who was right?</h1>
      <p className="lede">
        A model claim is only worth what it earns on data it never saw. Here is the model
        against an explicit baseline, on {evaluation.n_eval} held-out future matches — leakage
        verified.
      </p>
      <p className="verdict">
        On log-loss, the model{" "}
        {beats ? (
          <b>beats</b>
        ) : (
          <span style={{ color: "var(--bad)" }}>does not beat</span>
        )}{" "}
        its best baseline (<code>{best.label}</code>).
      </p>
      <div className="panel">
        <table>
          <thead>
            <tr>
              <th>Predictor</th>
              <th className="num">Log-loss</th>
              <th className="num">Accuracy</th>
              <th className="num">Brier</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <b>model</b>
              </td>
              <td className="num">{model.ll}</td>
              <td className="num">{model.acc}</td>
              <td className="num">{model.brier}</td>
            </tr>
            {evaluation.baselines.map((b) => {
              const m = fmt(b.metrics);
              return (
                <tr key={b.label}>
                  <td>{b.label}</td>
                  <td className="num">{m.ll}</td>
                  <td className="num">{m.acc}</td>
                  <td className="num">{m.brier}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <ProvenanceLine p={evaluation.provenance} />
    </>
  );
}
