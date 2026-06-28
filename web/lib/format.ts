// Small, pure formatting helpers shared across views.

export const pct = (v: number, digits = 0) => `${(v * 100).toFixed(digits)}%`;

export const elo = (v: number) => Math.round(v).toLocaleString("en-US");

export const score = (v: number, digits = 3) => v.toFixed(digits);

export const shortDate = (iso?: string | null) => (iso ? iso.slice(0, 10) : "—");

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
/** Compact "Apr 2026" form for tight figures. */
export const monthYear = (iso?: string | null) => {
  if (!iso) return "—";
  const [y, m] = iso.slice(0, 10).split("-");
  return `${MONTHS[Number(m) - 1] ?? m} ${y}`;
};

export type Conf = "high" | "medium" | "low" | string;

export const confColor = (c: Conf): string => {
  switch (c) {
    case "high":
      return "var(--color-conf-high)";
    case "medium":
      return "var(--color-conf-medium)";
    default:
      return "var(--color-conf-low)";
  }
};

/** 1–3 filled bars for a confidence signal indicator. */
export const confLevel = (c: Conf): number => (c === "high" ? 3 : c === "medium" ? 2 : 1);

/** Plain-language gloss so a number on screen actually means something. */
export const confWords = (c: Conf): string =>
  c === "high"
    ? "Plenty of recent club data behind this."
    : c === "medium"
      ? "A decent but not deep sample."
      : "Thin club history — read with caution.";

/** URL-safe team slug used in /team/[name] links. */
export const teamSlug = (name: string) => encodeURIComponent(name);
export const teamFromSlug = (slug: string) => decodeURIComponent(slug);
