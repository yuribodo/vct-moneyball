export function Unavailable({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="state">
      <strong>{title}</strong>
      <div style={{ marginTop: 6 }}>{detail}</div>
    </div>
  );
}
