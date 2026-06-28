"use client";

import Link from "next/link";
import { useReveal } from "@/components/motion/useReveal";
import { ScoreMeter } from "@/components/charts/ScoreMeter";
import { ConfidenceSignal } from "@/components/ui/Badge";
import { Flag } from "@/components/ui/Flag";
import type { RankingTeam } from "@/lib/api";
import { elo, teamSlug } from "@/lib/format";

const TIER_LABELS = ["Front-runners", "In the mix", "Outsiders"];

// Split the field into tiers at its two widest Elo gaps, so the ranking reads as
// "bands of near-equals" instead of implying 16 precisely separable teams.
function tierStarts(scores: number[]): Map<number, string> {
  const starts = new Map<number, string>();
  if (scores.length < 4) return starts;
  const gaps = scores.slice(1).map((s, i) => ({ at: i + 1, gap: scores[i] - s }));
  const cuts = [...gaps]
    .sort((a, b) => b.gap - a.gap)
    .slice(0, 2)
    .map((g) => g.at)
    .sort((a, b) => a - b);
  starts.set(0, TIER_LABELS[0]);
  cuts.forEach((at, i) => starts.set(at, TIER_LABELS[i + 1]));
  return starts;
}

export function RankingList({
  teams,
  source,
}: {
  teams: RankingTeam[];
  source: "roster" | "power";
}) {
  const scores = teams.map((t) => t.score);
  const lo = Math.min(...scores);
  const hi = Math.max(...scores);
  const span = hi - lo || 1;
  const norm = (s: number) => 0.18 + 0.82 * ((s - lo) / span);
  const unit = source === "roster" ? "Elo" : "Score";
  const tiers = tierStarts(scores);

  const ref = useReveal<HTMLDivElement>({ selector: ".rank-row", stagger: 0.04, y: 18 });

  return (
    <div ref={ref}>
      <div className="mb-1 grid grid-cols-[2.5rem_1fr_8rem] items-end gap-4 border-b border-ink/15 pb-2 sm:grid-cols-[3rem_minmax(0,1fr)_10rem_7rem]">
        <span className="label text-ink-3">#</span>
        <span className="label text-ink-3">Nation · strength</span>
        <span className="label text-right text-ink-3">{unit}</span>
        <span className="label hidden text-right text-ink-3 sm:block">Data</span>
      </div>

      {teams.map((t, i) => (
        <div key={t.team}>
          {tiers.has(i) ? (
            <div className="flex items-center gap-3 pb-1 pt-5 first:pt-2">
              <span className="label text-red">{tiers.get(i)}</span>
              <span className="h-px flex-1 bg-ink/15" />
            </div>
          ) : null}
          <Link href={`/team/${teamSlug(t.team)}`} className="rank-row group block">
            <div className="tick grid grid-cols-[2.5rem_1fr_8rem] items-center gap-4 border-b border-ink/10 py-3.5 transition-colors duration-150 group-hover:tick-on group-hover:bg-bone-2 sm:grid-cols-[3rem_minmax(0,1fr)_10rem_7rem]">
              <span className={`display text-3xl tnum ${i === 0 ? "text-red" : "text-ink"}`}>
                {String(t.position).padStart(2, "0")}
              </span>

              <div className="flex min-w-0 items-center gap-3">
                <Flag name={t.team} />
                <div className="min-w-0 flex-1">
                  <div className="display truncate text-xl leading-none text-ink">{t.team}</div>
                  <div className="mt-2 max-w-[15rem]">
                    <ScoreMeter value={norm(t.score)} lead={i === 0} />
                  </div>
                </div>
              </div>

              <div className="text-right">
                <span className="display text-2xl tnum text-ink">
                  {source === "roster" ? elo(t.score) : t.score.toFixed(3)}
                </span>
              </div>

              <div className="hidden justify-self-end sm:block">
                <ConfidenceSignal confidence={t.confidence} />
              </div>
            </div>
          </Link>
        </div>
      ))}
    </div>
  );
}
