import type { Provenance } from "@/lib/api";

// One quiet line of lineage. No glyphs, no code-block chips — just small caps
// labels and values, because every figure on the site should be auditable.
export function ProvenanceLine({ p }: { p: Provenance }) {
  const parts: string[] = [];
  if (p.version) parts.push(`version ${p.version}`);
  if (p.run_id) parts.push(`run ${p.run_id.slice(0, 12)}`);
  if (p.as_of) parts.push(`as of ${p.as_of.slice(0, 10)}`);
  if (p.feature_fingerprint) parts.push(`fingerprint ${p.feature_fingerprint.slice(0, 8)}`);

  return (
    <p className="mt-8 border-t border-ink/12 pt-3 text-xs tracking-wide text-ink-3">
      <span className="label !text-[0.6rem] text-ink-2">Source</span>{" "}
      <span className="text-ink-2">{p.source.replace("_", " ")}</span>
      {parts.map((part) => (
        <span key={part}> · {part}</span>
      ))}
    </p>
  );
}
