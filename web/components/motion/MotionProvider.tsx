"use client";

import { useEffect } from "react";
import { gsap, ScrollTrigger } from "./gsap";

// Mounted once in the root layout: sets global GSAP defaults and refreshes
// ScrollTrigger after hydration so pinned/scroll-driven sections measure correctly.
export function MotionProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    gsap.defaults({ ease: "power3.out", duration: 0.7 });
    const id = requestAnimationFrame(() => ScrollTrigger.refresh());
    return () => cancelAnimationFrame(id);
  }, []);

  return <>{children}</>;
}
