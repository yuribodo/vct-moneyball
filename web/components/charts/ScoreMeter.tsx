"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";

// Solid strength bar on a bone track. `value` normalised to [0,1].
export function ScoreMeter({ value, lead = false }: { value: number; lead?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(".meter-fill", {
          scaleX: 0,
          transformOrigin: "left center",
          duration: 0.8,
          ease: "power3.out",
          scrollTrigger: { trigger: ref.current, start: "top 92%" },
        });
      });
      return () => mm.revert();
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className="h-2 w-full bg-bone-3">
      <div
        className="meter-fill h-full"
        style={{
          width: `${Math.max(3, value * 100)}%`,
          background: lead ? "var(--color-red)" : "var(--color-ink)",
        }}
      />
    </div>
  );
}
