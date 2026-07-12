import type { Evaluation } from "@/lib/api";

const LABELS: Record<string, string> = {
  "winrate-elo": "Elo baseline",
  coin: "Coin flip",
};

export function MetricsTable({ evaluation }: { evaluation: Evaluation }) {
  const rows = [
    { label: "The model", m: evaluation.model_metrics, highlight: true },
    ...evaluation.baselines.map((b) => ({
      label: LABELS[b.label] ?? b.label,
      m: b.metrics,
      highlight: false,
    })),
  ];

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-ink/20 text-left">
          <th className="label py-2.5 pr-3 text-ink-3">Predictor</th>
          <th className="label py-2.5 px-3 text-right text-ink-3">Log-loss</th>
          <th className="label py-2.5 px-3 text-right text-ink-3">Accuracy</th>
          <th className="label py-2.5 px-3 text-right text-ink-3">Brier</th>
          <th className="label py-2.5 px-3 text-right text-ink-3">Calib. err</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.label} className={`border-b border-ink/10 ${r.highlight ? "bg-bone-2" : ""}`}>
            <td className={`py-3 pr-3 ${r.highlight ? "display text-base text-red" : "text-ink"}`}>
              {r.label}
            </td>
            <td className="py-3 px-3 text-right tnum text-ink">{r.m.log_loss.toFixed(4)}</td>
            <td className="py-3 px-3 text-right tnum text-ink">{(r.m.accuracy * 100).toFixed(1)}%</td>
            <td className="py-3 px-3 text-right tnum text-ink">{r.m.brier.toFixed(4)}</td>
            <td className="py-3 px-3 text-right tnum text-ink">
              {r.m.calibration_error != null ? r.m.calibration_error.toFixed(4) : "—"}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
