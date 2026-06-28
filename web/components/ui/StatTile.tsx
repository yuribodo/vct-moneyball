import { clsx } from "@/lib/clsx";

// A labelled figure. Big condensed number, label above, optional gloss below
// so the figure is never just a naked number nobody can read.
export function StatTile({
  label,
  value,
  sub,
  emphasis = false,
  className,
}: {
  label: string;
  value: React.ReactNode;
  sub?: string;
  emphasis?: boolean;
  className?: string;
}) {
  return (
    <div className={clsx("border-t-2 pt-3", emphasis ? "border-red" : "border-ink", className)}>
      <div className="label text-ink-3">{label}</div>
      <div className="display mt-1.5 text-4xl tnum text-ink">{value}</div>
      {sub ? <div className="mt-1 text-xs leading-snug text-ink-3">{sub}</div> : null}
    </div>
  );
}
