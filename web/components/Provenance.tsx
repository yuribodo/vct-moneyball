import type { Provenance } from "@/lib/api";

export function ProvenanceLine({ p }: { p: Provenance }) {
  const parts: React.ReactNode[] = [];
  if (p.version) parts.push(<span key="v">version <code>{p.version}</code></span>);
  if (p.run_id) parts.push(<span key="r">run <code>{p.run_id.slice(0, 12)}</code></span>);
  if (p.as_of) parts.push(<span key="a">as of <code>{p.as_of.slice(0, 10)}</code></span>);
  if (p.feature_fingerprint)
    parts.push(<span key="f">fingerprint <code>{p.feature_fingerprint.slice(0, 8)}</code></span>);
  return (
    <p className="prov">
      Provenance — {p.source.replace("_", " ")}
      {parts.map((node, i) => (
        <span key={i}> · {node}</span>
      ))}
    </p>
  );
}
