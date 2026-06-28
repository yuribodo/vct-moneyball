// Pure helpers for hand-rolled SVG charts.

export type Pt = { x: number; y: number };

const round2 = (n: number) => Math.round(n * 100) / 100;

/** Point on a circle for a radar/polar chart. angleIndex/total places it; 0 = top.
 *  Coordinates are rounded to 2dp so server/client render byte-identical SVG (no
 *  float-precision hydration mismatch). */
export function polar(cx: number, cy: number, r: number, angleIndex: number, total: number): Pt {
  const a = (angleIndex / total) * Math.PI * 2 - Math.PI / 2;
  return { x: round2(cx + r * Math.cos(a)), y: round2(cy + r * Math.sin(a)) };
}

export function pointsToPath(points: Pt[], close = true): string {
  if (!points.length) return "";
  const d = points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)},${p.y.toFixed(2)}`);
  return d.join(" ") + (close ? " Z" : "");
}

/** Normalise values to [0,1] within a domain (defaults to data min/max with padding). */
export function normalize(values: number[], domain?: [number, number]): number[] {
  const lo = domain ? domain[0] : Math.min(...values);
  const hi = domain ? domain[1] : Math.max(...values);
  const span = hi - lo || 1;
  return values.map((v) => (v - lo) / span);
}
