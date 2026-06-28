// A plain editorial rule (no glow). Kept the export name for call sites.
export function GlowDivider({ className = "" }: { className?: string }) {
  return <div className={`h-px w-full bg-ink/15 ${className}`} />;
}

// Section header: a red tick, a kicker, a big condensed title, optional standfirst.
// Left-aligned, asymmetric — not centered.
export function SectionHeading({
  kicker,
  title,
  children,
}: {
  kicker?: string;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="mb-10 max-w-3xl">
      {kicker ? (
        <div className="mb-3 flex items-center gap-3">
          <span className="h-3 w-6 bg-red" />
          <span className="label text-ink-2">{kicker}</span>
        </div>
      ) : null}
      <h1 className="display text-5xl text-ink sm:text-6xl">{title}</h1>
      {children ? (
        <p className="mt-4 max-w-2xl text-[1.05rem] leading-relaxed text-ink-2">{children}</p>
      ) : null}
    </div>
  );
}
