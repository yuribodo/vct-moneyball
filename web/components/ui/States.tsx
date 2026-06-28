export function EmptyState({
  kicker = "Unavailable",
  title,
  children,
}: {
  kicker?: string;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="max-w-xl border-l-2 border-red pl-6">
      <p className="label text-red">{kicker}</p>
      <h2 className="display mt-2 text-3xl text-ink">{title}</h2>
      {children ? <div className="mt-3 text-ink-2">{children}</div> : null}
    </div>
  );
}
