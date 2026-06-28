export function Empty({
  kicker,
  title,
  children,
}: {
  kicker: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="empty">
      <p className="kicker">{kicker}</p>
      <h2>{title}</h2>
      <p>{children}</p>
    </div>
  );
}
