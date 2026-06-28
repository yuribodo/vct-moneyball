export function Badge({ confidence }: { confidence: string }) {
  return <span className={`badge ${confidence}`}>{confidence}</span>;
}
