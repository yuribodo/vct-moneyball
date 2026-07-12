"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";

export type BarRow = { label: string; value: number; highlight?: boolean };

// Grouped horizontal bars. Highlighted row in red, rest in ink. Solid fills.
export function BarCompare({
  rows,
  format = (v) => v.toFixed(3),
  max,
}: {
  rows: BarRow[];
  format?: (v: number) => string;
  max?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const hi = max ?? Math.max(...rows.map((r) => r.value)) * 1.1;

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(".bar-fill", {
          scaleX: 0,
          transformOrigin: "left center",
          stagger: 0.08,
          duration: 0.7,
          ease: "power3.out",
          scrollTrigger: { trigger: ref.current, start: "top 88%" },
        });
      });
      return () => mm.revert();
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className="space-y-3">
      {rows.map((r) => (
        <div key={r.label} className="grid grid-cols-[7rem_1fr_3.5rem] items-center gap-3">
          <span className={`label !text-[0.62rem] ${r.highlight ? "text-red" : "text-ink-3"}`}>
            {r.label}
          </span>
          <div className="h-3 bg-bone-3">
            <div
              className="bar-fill h-full"
              style={{
                width: `${Math.min(100, (r.value / hi) * 100)}%`,
                background: r.highlight ? "var(--color-red)" : "var(--color-ink-2)",
              }}
            />
          </div>
          <span className="text-right text-xs tnum text-ink">{format(r.value)}</span>
        </div>
      ))}
    </div>
  );
}
