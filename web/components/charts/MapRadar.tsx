"use client";

import { useRef } from "react";
import { gsap, useGSAP } from "@/components/motion/gsap";
import { polar, pointsToPath, normalize } from "./chart-utils";
import type { TeamMapScore } from "@/lib/api";

// 12-axis radar of per-map strength. Ink rings on bone, red shape. No neon dots.
export function MapRadar({ maps }: { maps: TeamMapScore[] }) {
  const ref = useRef<SVGSVGElement>(null);
  const size = 360;
  const cx = size / 2;
  const cy = size / 2;
  const rMax = size / 2 - 56;
  const total = maps.length;

  const norm = normalize(
    maps.map((m) => m.map_score),
    [
      Math.min(...maps.map((m) => m.map_score)) * 0.92,
      Math.max(...maps.map((m) => m.map_score)) * 1.04,
    ],
  );

  const dataPoints = maps.map((_, i) => polar(cx, cy, rMax * Math.max(0.12, norm[i]), i, total));
  const dataPath = pointsToPath(dataPoints);
  const rings = [0.25, 0.5, 0.75, 1];

  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(".radar-shape", {
          scale: 0.2,
          opacity: 0,
          transformOrigin: "center",
          duration: 0.8,
          ease: "power3.out",
        });
      });
      return () => mm.revert();
    },
    { scope: ref },
  );

  return (
    <svg ref={ref} viewBox={`0 0 ${size} ${size}`} className="mx-auto h-auto w-full max-w-sm">
      {rings.map((rr) => (
        <circle key={rr} cx={cx} cy={cy} r={rMax * rr} fill="none" stroke="#0f192322" strokeWidth={1} />
      ))}
      {maps.map((m, i) => {
        const end = polar(cx, cy, rMax, i, total);
        const label = polar(cx, cy, rMax + 24, i, total);
        return (
          <g key={m.map}>
            <line x1={cx} y1={cy} x2={end.x} y2={end.y} stroke="#0f19231a" strokeWidth={1} />
            <text
              x={label.x}
              y={label.y}
              textAnchor="middle"
              dominantBaseline="middle"
              fill="#6b7178"
              style={{ fontSize: 9, letterSpacing: 1, fontWeight: 600 }}
            >
              {m.map.toUpperCase()}
            </text>
          </g>
        );
      })}
      <path
        className="radar-shape"
        d={dataPath}
        fill="#ff465526"
        stroke="#ff4655"
        strokeWidth={2}
        strokeLinejoin="round"
      />
      {dataPoints.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={2.5} fill="#ff4655" />
      ))}
    </svg>
  );
}
