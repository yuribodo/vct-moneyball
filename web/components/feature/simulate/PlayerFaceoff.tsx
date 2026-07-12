import type { Prediction } from "@/lib/api";

export function PlayerFaceoff({ result }: { result: Prediction }) {
  const max = Math.max(result.contributors_a.length, result.contributors_b.length);
  const rows = Array.from({ length: max });

  return (
    <div className="mt-8">
      <div className="mb-3 flex items-center justify-between">
        <span className="label text-red">{result.team_a} — key players</span>
        <span className="label text-ink">{result.team_b} — key players</span>
      </div>
      <div className="divide-y divide-ink/10 border-y border-ink/15">
        {rows.map((_, i) => (
          <div key={i} className="grid grid-cols-2 items-center py-2 text-sm">
            <span className="text-ink">{result.contributors_a[i] ?? "—"}</span>
            <span className="text-right text-ink">{result.contributors_b[i] ?? "—"}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
