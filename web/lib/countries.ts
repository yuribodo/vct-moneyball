// Country name -> ISO alpha-2 (for flag emoji). Covers the 16 ENC 2026 nations
// plus common opponents; unknown names fall back to a neutral marker.

const ISO: Record<string, string> = {
  "South Korea": "KR",
  China: "CN",
  "Great Britain": "GB",
  Finland: "FI",
  "United States of America": "US",
  Singapore: "SG",
  Malaysia: "MY",
  Thailand: "TH",
  Philippines: "PH",
  Türkiye: "TR",
  Turkey: "TR",
  Poland: "PL",
  Chile: "CL",
  Brazil: "BR",
  Canada: "CA",
  Lithuania: "LT",
  "Chinese Taipei": "TW",
  Japan: "JP",
  France: "FR",
  Germany: "DE",
  Spain: "ES",
  Indonesia: "ID",
  Vietnam: "VN",
  India: "IN",
};

export function iso2(name: string | null | undefined): string | null {
  if (!name) return null;
  return ISO[name] ?? null;
}

/** Regional-indicator flag emoji from an ISO code, e.g. "KR" -> 🇰🇷. */
export function flagEmoji(name: string | null | undefined): string {
  const code = iso2(name);
  if (!code) return "🏳";
  return code
    .toUpperCase()
    .replace(/./g, (c) => String.fromCodePoint(127397 + c.charCodeAt(0)));
}

/** Short 3-letter code for compact UI (falls back to first letters of the name). */
export function shortCode(name: string): string {
  const code = iso2(name);
  if (code) return code;
  return name
    .split(/\s+/)
    .map((w) => w[0])
    .join("")
    .slice(0, 3)
    .toUpperCase();
}
