"use client";

import { Flag } from "@/components/ui/Flag";
import { clsx } from "@/lib/clsx";
import { pct } from "@/lib/format";
import type { Matrix } from "@/lib/api";
import type { BracketMatch as BMatch } from "@/lib/bracket";

export function BracketMatch({ match, teams }: { match: BMatch; teams: Matrix["teams"] }) {
  const aWon = match.winner === match.a;
  const rows = [
    { idx: match.a, p: match.pA, won: aWon },
    { idx: match.b, p: 1 - match.pA, won: !aWon },
  ];

  return (
    <div className="bracket-match w-48 border border-ink/15 bg-paper">
      {rows.map((row, i) => {
        const t = teams[row.idx];
        return (
          <div
            key={i}
            className={clsx(
              "flex items-center gap-2 px-2.5 py-2 text-sm",
              i === 0 && "border-b border-ink/10",
              row.won ? "bg-bone-2" : "opacity-50",
            )}
          >
            <Flag name={t.team} size="sm" />
            <span className={clsx("min-w-0 flex-1 truncate", row.won ? "display text-ink" : "text-ink-2")}>
              {t.team}
            </span>
            <span className={clsx("text-xs tnum", row.won ? "text-red" : "text-ink-3")}>{pct(row.p)}</span>
          </div>
        );
      })}
    </div>
  );
}
