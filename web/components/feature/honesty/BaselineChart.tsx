"use client";

import { BarCompare, type BarRow } from "@/components/charts/BarCompare";
import type { Evaluation } from "@/lib/api";

const LABELS: Record<string, string> = { "winrate-elo": "Elo", coin: "Coin flip" };

// Log-loss is the headline — lower is better; the model bar is highlighted.
export function BaselineChart({ evaluation }: { evaluation: Evaluation }) {
  const rows: BarRow[] = [
    { label: "Model", value: evaluation.model_metrics.log_loss, highlight: true },
    ...evaluation.baselines.map((b) => ({
      label: LABELS[b.label] ?? b.label,
      value: b.metrics.log_loss,
    })),
  ];

  return (
    <div className="border-t-2 border-ink pt-4">
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="display text-lg text-ink">Log-loss</h3>
        <span className="label text-ink-3">lower is better</span>
      </div>
      <p className="mb-4 text-sm text-ink-3">
        How badly each predictor is surprised by real results. Shorter bar = better calls.
      </p>
      <BarCompare rows={rows} format={(v) => v.toFixed(4)} />
    </div>
  );
}
