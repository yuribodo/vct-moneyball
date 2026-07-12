"use client";

import { useReveal } from "@/components/motion/useReveal";
import { ConfidenceSignal } from "@/components/ui/Badge";
import type { TeamContributor } from "@/lib/api";
import { normalize } from "@/components/charts/chart-utils";

export function RosterGrid({ contributors }: { contributors: TeamContributor[] }) {
  const sorted = [...contributors].sort((a, b) => b.player_score - a.player_score);
  const norm = normalize(
    sorted.map((c) => c.player_score),
    [
      Math.min(...sorted.map((c) => c.player_score)) * 0.9,
      Math.max(...sorted.map((c) => c.player_score)) * 1.03,
    ],
  );
  const ref = useReveal<HTMLDivElement>({ selector: ".player-row", stagger: 0.04, y: 14 });

  return (
    <div ref={ref}>
      {sorted.map((c, i) => (
        <div
          key={c.player}
          className="player-row tick flex items-center gap-4 border-b border-ink/10 py-3 first:border-t"
        >
          <span className="display w-6 text-center text-lg tnum text-ink-3">{i + 1}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="display text-lg leading-none text-ink">{c.player}</span>
              {c.low_history_baseline ? (
                <span className="label !text-[0.55rem] text-conf-medium">thin history</span>
              ) : null}
            </div>
            <div className="mt-2 h-1.5 w-full bg-bone-3">
              <div
                className="h-full"
                style={{
                  width: `${Math.max(5, norm[i] * 100)}%`,
                  background: i === 0 ? "var(--color-red)" : "var(--color-ink)",
                }}
              />
            </div>
          </div>
          <div className="text-right">
            <div className="display text-lg tnum text-ink">{c.player_score.toFixed(3)}</div>
            <div className="text-[0.65rem] text-ink-3">{c.maps_played} maps</div>
          </div>
          <div className="hidden sm:block">
            <ConfidenceSignal confidence={c.confidence} showLabel={false} />
          </div>
        </div>
      ))}
    </div>
  );
}
