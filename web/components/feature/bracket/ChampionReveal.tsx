"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { Flag } from "@/components/ui/Flag";
import type { Matrix } from "@/lib/api";

// Solid red block, no glow/spotlight. The payoff is type + colour weight.
export function ChampionReveal({ team }: { team: Matrix["teams"][number] }) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(ref.current, { opacity: 0, x: 24, duration: 0.6, ease: "power3.out", delay: 0.3 });
      });
      return () => mm.revert();
    },
    { scope: ref, dependencies: [team.team] },
  );

  return (
    <div ref={ref} className="cut-tl flex w-52 flex-col gap-2 bg-red px-6 py-7 text-bone">
      <span className="label text-bone/70">Predicted champion</span>
      <Flag name={team.team} size="lg" />
      <div className="display text-3xl leading-none">{team.team}</div>
    </div>
  );
}
