"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { ProbabilityBar } from "@/components/charts/ProbabilityBar";
import { PlayerFaceoff } from "./PlayerFaceoff";
import { ProvenanceLine } from "@/components/ui/ProvenanceLine";
import { Flag } from "@/components/ui/Flag";
import type { Prediction } from "@/lib/api";
import { elo, pct } from "@/lib/format";

export function VersusReveal({ result }: { result: Prediction }) {
  const ref = useRef<HTMLDivElement>(null);
  const aWins = result.winner === result.team_a;
  const winP = aWins ? result.p_a : result.p_b;

  // Plain-language read of the margin.
  const margin =
    winP >= 0.65 ? "are clear favourites" : winP >= 0.55 ? "are favoured" : "have a slight edge";

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const tl = gsap.timeline();
        tl.from(".vs-card-a", { xPercent: -40, opacity: 0, duration: 0.5, ease: "power3.out" })
          .from(".vs-card-b", { xPercent: 40, opacity: 0, duration: 0.5, ease: "power3.out" }, "<")
          .from(".vs-verdict", { opacity: 0, y: 12, duration: 0.5 }, "+=0.1");
      });
      return () => mm.revert();
    },
    { scope: ref, dependencies: [result.team_a, result.team_b, result.p_a] },
  );

  return (
    <div ref={ref} className="mt-10 border-t-2 border-ink pt-8">
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4">
        <div className="vs-card-a flex flex-col items-center gap-1.5 text-center">
          <Flag name={result.team_a} size="lg" />
          <div className="display text-xl text-ink">{result.team_a}</div>
          <div className="text-xs text-ink-3">{elo(result.elo_a)} roster Elo</div>
        </div>
        <span className="display text-2xl text-ink-3">VS</span>
        <div className="vs-card-b flex flex-col items-center gap-1.5 text-center">
          <Flag name={result.team_b} size="lg" />
          <div className="display text-xl text-ink">{result.team_b}</div>
          <div className="text-xs text-ink-3">{elo(result.elo_b)} roster Elo</div>
        </div>
      </div>

      <div className="mt-8">
        <ProbabilityBar pA={result.p_a} labelA={result.team_a} labelB={result.team_b} />
      </div>

      <p className="vs-verdict mt-6 max-w-2xl text-lg leading-relaxed text-ink-2">
        <span className="display text-2xl text-red">{result.winner}</span> {margin} — the model gives
        them a <span className="text-ink">{pct(winP)}</span> chance, based only on club form up to{" "}
        {result.as_of.slice(0, 10)}.
        {result.low_confidence ? (
          <span className="mt-2 block text-sm text-conf-medium">
            Soft read: at least one roster has thin club history, so treat this as a lean, not a lock.
          </span>
        ) : null}
      </p>

      <PlayerFaceoff result={result} />
      <ProvenanceLine p={result.provenance} />
    </div>
  );
}
