"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api, ApiError, type Matrix } from "@/lib/api";
import { simulateBracket, titleOdds, type BracketResult } from "@/lib/bracket";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { BracketMatch } from "./BracketMatch";
import { ChampionReveal } from "./ChampionReveal";
import { Button } from "@/components/ui/Button";
import { Skeleton } from "@/components/ui/Skeleton";
import { EmptyState } from "@/components/ui/States";
import { ProvenanceLine } from "@/components/ui/ProvenanceLine";
import { Flag } from "@/components/ui/Flag";
import { pct } from "@/lib/format";
import { clsx } from "@/lib/clsx";

type Mode = "deterministic" | "probabilistic";

export function Bracket() {
  const [matrix, setMatrix] = useState<Matrix | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("deterministic");
  const [seed, setSeed] = useState(0);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api
      .matrix("2026-11-08")
      .then(setMatrix)
      .catch((e: ApiError) => setError(e.message));
  }, []);

  const result: BracketResult | null = useMemo(() => {
    if (!matrix) return null;
    void seed;
    return simulateBracket(matrix, mode);
  }, [matrix, mode, seed]);

  const odds = useMemo(() => (matrix ? titleOdds(matrix, 2000).slice(0, 6) : []), [matrix]);

  useGSAP(
    () => {
      if (!result) return;
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(".bracket-col", { opacity: 0, x: -20, stagger: 0.1, duration: 0.45, ease: "power3.out" });
      });
      return () => mm.revert();
    },
    { scope: ref, dependencies: [result, mode, seed] },
  );

  if (error) {
    return (
      <EmptyState kicker="Bracket unavailable" title="Couldn't build the bracket">
        {error}
      </EmptyState>
    );
  }

  if (!matrix || !result) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="flex gap-6 overflow-hidden">
          {[8, 4, 2, 1].map((n, c) => (
            <div key={c} className="flex flex-col justify-around gap-3">
              {Array.from({ length: n }).map((_, i) => (
                <Skeleton key={i} className="h-14 w-48" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  const champion = matrix.teams[result.champion];

  return (
    <div ref={ref}>
      <div className="mb-2 flex flex-wrap items-center gap-3">
        <div className="inline-flex border border-ink/20">
          {(["deterministic", "probabilistic"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={clsx(
                "display px-4 py-2 text-sm transition-colors",
                mode === m ? "bg-ink text-bone" : "text-ink-3 hover:text-ink",
              )}
            >
              {m === "deterministic" ? "Most likely" : "Coin-flip"}
            </button>
          ))}
        </div>
        {mode === "probabilistic" ? <Button variant="ghost" onClick={() => setSeed((s) => s + 1)}>Re-simulate</Button> : null}
      </div>
      <p className="mb-8 max-w-2xl text-sm text-ink-3">
        {mode === "deterministic"
          ? "Each tie goes to the more likely side — the cleanest read of the field. The percentage on each line is that team's win chance for that match."
          : "Every tie is a weighted coin-flip on the model's odds, so upsets happen. Re-simulate to see how the bracket swings."}
      </p>

      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-max items-stretch gap-6">
          {result.rounds.map((round, ci) => (
            <div key={round.name} className="bracket-col flex flex-col justify-around gap-3">
              <div className="label mb-1 text-ink-3">{round.name}</div>
              {round.matches.map((m, i) => (
                <BracketMatch key={`${ci}-${i}`} match={m} teams={matrix.teams} />
              ))}
            </div>
          ))}
          <div className="flex items-center pl-2">
            <ChampionReveal team={champion} />
          </div>
        </div>
      </div>

      <div className="mt-12">
        <div className="mb-1 flex items-baseline justify-between border-b border-ink/15 pb-2">
          <h2 className="display text-2xl text-ink">Who actually lifts it</h2>
          <span className="label text-ink-3">2,000 coin-flip runs</span>
        </div>
        <p className="mt-3 mb-5 max-w-2xl text-sm text-ink-3">
          The single bracket above shows the likeliest path. Run it 2,000 times with upsets allowed
          and these are each nation&apos;s odds of winning the whole thing.
        </p>
        <div className="grid gap-px bg-ink/15 sm:grid-cols-2 lg:grid-cols-3">
          {odds.map((o, i) => {
            const t = matrix.teams[o.index];
            return (
              <div key={t.team} className="flex items-center gap-3 bg-bone px-4 py-3">
                <span className="display w-5 tnum text-ink-3">{i + 1}</span>
                <Flag name={t.team} size="sm" />
                <span className="min-w-0 flex-1 truncate text-sm text-ink">{t.team}</span>
                <span className="display tnum text-red">{pct(o.odds, 1)}</span>
              </div>
            );
          })}
        </div>
      </div>

      <ProvenanceLine p={matrix.provenance} />
    </div>
  );
}
