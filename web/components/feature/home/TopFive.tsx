"use client";

import Link from "next/link";
import { useReveal } from "@/components/motion/useReveal";
import { Flag } from "@/components/ui/Flag";
import type { RankingTeam } from "@/lib/api";
import { elo, teamSlug } from "@/lib/format";

export function TopFive({ teams }: { teams: RankingTeam[] }) {
  const ref = useReveal<HTMLDivElement>({ selector: ".top-row", stagger: 0.06, y: 16 });

  return (
    <div ref={ref}>
      {teams.map((t, i) => (
        <Link
          key={t.team}
          href={`/team/${teamSlug(t.team)}`}
          className="top-row tick group flex items-center gap-4 border-b border-ink/12 py-3.5 transition-colors duration-150 hover:tick-on hover:bg-bone-2"
        >
          <span className={`display text-2xl tnum ${i === 0 ? "text-red" : "text-ink-3"}`}>
            {String(t.position).padStart(2, "0")}
          </span>
          <Flag name={t.team} />
          <span className="display flex-1 text-lg text-ink">{t.team}</span>
          <span className="display text-xl tnum text-ink">{elo(t.score)}</span>
        </Link>
      ))}
    </div>
  );
}
