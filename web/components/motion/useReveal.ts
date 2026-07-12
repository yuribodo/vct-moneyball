"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "./gsap";

type RevealOpts = {
  /** Selector for children to stagger in. If omitted, the container itself animates. */
  selector?: string;
  y?: number;
  stagger?: number;
  duration?: number;
  delay?: number;
  start?: string;
};

/**
 * Scroll-triggered reveal. Returns a ref to attach to the scope container.
 * Wrapped in gsap.matchMedia so it no-ops under prefers-reduced-motion.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(opts: RevealOpts = {}) {
  const ref = useRef<T>(null);
  const {
    selector,
    y = 28,
    stagger = 0.06,
    duration = 0.7,
    delay = 0,
    start = "top 85%",
  } = opts;

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        const targets = selector ? gsap.utils.toArray(selector) : [ref.current];
        gsap.from(targets as gsap.TweenTarget, {
          opacity: 0,
          y,
          duration,
          delay,
          stagger,
          ease: "power3.out",
          scrollTrigger: { trigger: ref.current, start },
        });
      });
      return () => mm.revert();
    },
    { scope: ref },
  );

  return ref;
}
