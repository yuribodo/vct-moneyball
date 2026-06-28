import type { Provenance } from "@/lib/api";

export function ProvenanceLine({ p }: { p: Provenance }) {
  return (
    <p className="prov">
      Provenance — {p.source}
      {p.version ? (
        <>
          {" · "}version <code>{p.version}</code>
        </>
      ) : null}
      {p.run_id ? (
        <>
          {" · "}run <code>{p.run_id.slice(0, 12)}</code>
        </>
      ) : null}
      {p.as_of ? (
        <>
          {" · "}as of <code>{p.as_of.slice(0, 10)}</code>
        </>
      ) : null}
    </p>
  );
}
