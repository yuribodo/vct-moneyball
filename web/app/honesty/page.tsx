import { api, ApiError } from "@/lib/api";
import { MetricsTable } from "@/components/feature/honesty/MetricsTable";
import { BaselineChart } from "@/components/feature/honesty/BaselineChart";
import { StatTile } from "@/components/ui/StatTile";
import { ProvenanceLine } from "@/components/ui/ProvenanceLine";
import { EmptyState } from "@/components/ui/States";
import { SectionHeading } from "@/components/ui/GlowDivider";
import { monthYear } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function HonestyPage() {
  let ev;
  try {
    ev = await api.evaluation("bridge");
  } catch (e) {
    return (
      <div className="py-20">
        <EmptyState kicker="Unavailable" title="No evaluation published yet">
          {(e as ApiError).message}
        </EmptyState>
      </div>
    );
  }

  const baselineLL = Math.min(...ev.baselines.map((b) => b.metrics.log_loss));
  const beats = ev.model_metrics.log_loss < baselineLL;

  return (
    <div className="py-12 sm:py-16">
      <SectionHeading kicker="The Reckoning" title="Does it actually work?">
        Anyone can post a prediction. The test is whether it holds up on matches the model never saw
        while training. It does — here are the receipts, with no leakage and no cherry-picking.
      </SectionHeading>

      <div className="mb-14 grid max-w-3xl grid-cols-2 gap-x-10 gap-y-6 sm:grid-cols-4">
        <StatTile label="Tested on" value={ev.n_eval} sub="unseen matches" emphasis />
        <StatTile label="Trained on" value={ev.n_train} sub="earlier matches" />
        <StatTile label="Leakage" value={ev.leakage_verified ? "None" : "?"} sub="time-split verified" />
        <StatTile label="Cutoff" value={monthYear(ev.cutoff)} sub="train / test split" />
      </div>

      <div className="grid gap-14 lg:grid-cols-[1.3fr_1fr]">
        <section>
          <div className="mb-4 flex items-baseline justify-between border-b border-ink/15 pb-2">
            <h2 className="display text-2xl text-ink">Model vs. baselines</h2>
            <span className="label text-ink-3">unseen matches</span>
          </div>
          <MetricsTable evaluation={ev} />
          <p className="mt-4 max-w-xl text-sm leading-relaxed text-ink-3">
            The model {beats ? "beats" : "trails"} both a plain Elo baseline and a 50/50 coin flip on
            log-loss — the standard test of whether forecasts are genuinely informative.
          </p>
        </section>
        <section>
          <BaselineChart evaluation={ev} />
        </section>
      </div>

      <ProvenanceLine p={ev.provenance} />
    </div>
  );
}
