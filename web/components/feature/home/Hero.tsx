"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { ButtonLink } from "@/components/ui/Button";

export function Hero() {
  const ref = useRef<HTMLDivElement>(null);

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const tl = gsap.timeline();
        tl.from(".hero-kicker", { opacity: 0, y: 14, duration: 0.5 })
          .from(".hero-line", { opacity: 0, y: 30, duration: 0.6, stagger: 0.08 }, "-=0.2")
          .from(".hero-sub", { opacity: 0, y: 14, duration: 0.5 }, "-=0.3")
          .from(".hero-cta", { opacity: 0, y: 12, stagger: 0.07, duration: 0.4 }, "-=0.2");
      });
      return () => mm.revert();
    },
    { scope: ref },
  );

  return (
    <div ref={ref} className="relative pt-16 sm:pt-24">
      <div className="hero-kicker mb-4 flex items-center gap-3">
        <span className="h-3 w-8 bg-red" />
        <span className="label text-ink-2">ENC 2026 · Power Index & Match Engine</span>
      </div>
      <h1 className="display text-ink">
        <span className="hero-line block text-[clamp(3rem,10vw,8rem)]">Sixteen nations.</span>
        <span className="hero-line block text-[clamp(3rem,10vw,8rem)]">
          One <span className="text-red">number</span> each.
        </span>
      </h1>
      <p className="hero-sub mt-7 max-w-xl text-lg leading-relaxed text-ink-2">
        A locked, leakage-checked model that ranks every ENC 2026 roster, simulates any matchup, and
        runs the whole bracket to a predicted champion. Dated and frozen before a map is played.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <ButtonLink href="/simulate" variant="primary" className="hero-cta">
          Simulate a match
        </ButtonLink>
        <ButtonLink href="/bracket" variant="solid" className="hero-cta">
          Run the bracket
        </ButtonLink>
        <ButtonLink href="/rankings" variant="ghost" className="hero-cta">
          See the board
        </ButtonLink>
      </div>
    </div>
  );
}
