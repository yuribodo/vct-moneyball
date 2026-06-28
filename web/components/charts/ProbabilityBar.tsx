"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { pct } from "@/lib/format";

// Head-to-head split: favourite in red, underdog in ink. Solid fills, no
// gradient. The winning side reads instantly by colour weight.
export function ProbabilityBar({
  pA,
  labelA,
  labelB,
  animate = true,
}: {
  pA: number;
  labelA: string;
  labelB: string;
  animate?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const pB = 1 - pA;
  const aLeads = pA >= pB;

  useGSAP(
    () => {
      if (!animate) return;
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(".prob-fill-a", { width: "50%", duration: 0.9, ease: "power3.out" });
        gsap.from(".prob-fill-b", { width: "50%", duration: 0.9, ease: "power3.out" });
        gsap.from(".prob-num", { opacity: 0, duration: 0.4, delay: 0.4, stagger: 0.08 });
      });
      return () => mm.revert();
    },
    { scope: ref, dependencies: [pA] },
  );

  return (
    <div ref={ref}>
      <div className="mb-2 flex items-center justify-between">
        <span className={`display text-base ${aLeads ? "text-red" : "text-ink-3"}`}>{labelA}</span>
        <span className={`display text-base ${!aLeads ? "text-ink" : "text-ink-3"}`}>{labelB}</span>
      </div>
      <div className="flex h-11 w-full overflow-hidden">
        <div
          className="prob-fill-a flex items-center justify-start px-3"
          style={{ width: pct(pA, 2), background: aLeads ? "var(--color-red)" : "var(--color-red-deep)" }}
        >
          <span className="prob-num display text-lg tnum text-bone">{pct(pA)}</span>
        </div>
        <div
          className="prob-fill-b flex items-center justify-end px-3"
          style={{ width: pct(pB, 2), background: !aLeads ? "var(--color-ink)" : "var(--color-ink-2)" }}
        >
          <span className="prob-num display text-lg tnum text-bone">{pct(pB)}</span>
        </div>
      </div>
    </div>
  );
}
