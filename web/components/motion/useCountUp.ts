"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "./gsap";

/**
 * Animates a number from 0 → value when scrolled into view.
 * Returns a ref for the element whose textContent will be updated.
 */
export function useCountUp(value: number, decimals = 0, duration = 1.2) {
  const ref = useRef<HTMLSpanElement>(null);

  useGSAP(
    () => {
      const el = ref.current;
      if (!el) return;
      const obj = { n: 0 };
      const render = () => {
        el.textContent = obj.n.toLocaleString("en-US", {
          minimumFractionDigits: decimals,
          maximumFractionDigits: decimals,
        });
      };
      render();

      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.to(obj, {
          n: value,
          duration,
          ease: "power2.out",
          onUpdate: render,
          scrollTrigger: { trigger: el, start: "top 90%" },
        });
      });
      mm.add("(prefers-reduced-motion: reduce)", () => {
        obj.n = value;
        render();
      });
      return () => mm.revert();
    },
    { scope: ref, dependencies: [value] },
  );

  return ref;
}
