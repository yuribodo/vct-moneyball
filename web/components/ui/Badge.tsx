import { confColor, confLevel, separationWords, type Conf } from "@/lib/format";

// Confidence as a 3-bar signal (like reception strength) + label — reads
// instantly as "how sure are we", no generic pill-with-dot badge.
export function ConfidenceSignal({
  confidence,
  showLabel = true,
}: {
  confidence: Conf;
  showLabel?: boolean;
}) {
  const level = confLevel(confidence);
  const color = confColor(confidence);
  return (
    <span className="inline-flex items-center gap-2" title={`${confidence} confidence`}>
      <span className="flex items-end gap-[2px]" aria-hidden>
        {[1, 2, 3].map((b) => (
          <span
            key={b}
            className="w-[3px]"
            style={{
              height: `${4 + b * 3}px`,
              background: b <= level ? color : "var(--color-bone-3)",
            }}
          />
        ))}
      </span>
      {showLabel ? (
        <span
          className="label !text-[0.62rem]"
          style={{ color: level === 1 ? "var(--color-ink-3)" : color }}
        >
          {confidence}
        </span>
      ) : null}
    </span>
  );
}

// How close a team's rank is to its neighbor's — orthogonal to ConfidenceSignal
// (that's data volume; this is rank precision). Silent for "clear" since that's the
// unremarkable default — only flags the cases worth a second look.
export function SeparationTag({
  separation,
}: Readonly<{ separation?: string | null }>) {
  if (!separation || separation === "clear") return null;
  const color = separation === "razor-thin" ? "var(--color-red)" : "var(--color-conf-medium)";
  return (
    <span
      className="label !text-[0.62rem]"
      style={{ color }}
      title={separationWords(separation)}
    >
      {separation}
    </span>
  );
}

// Plain text tag, square, editorial — used for context chips.
export function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="label border border-ink/15 px-2 py-1 !text-[0.62rem] text-ink-2">
      {children}
    </span>
  );
}
