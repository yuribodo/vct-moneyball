import Link from "next/link";
import { Flag, CountryCode } from "./Flag";
import { clsx } from "@/lib/clsx";
import { teamSlug } from "@/lib/format";

// Compact team chip used in pickers/grids. Hover = red tick slides in + paper
// lift; selected = ink fill. No glowing borders.
export function TeamCard({
  name,
  position,
  selected = false,
  onClick,
  as = "link",
  className,
}: {
  name: string;
  position?: number;
  selected?: boolean;
  onClick?: () => void;
  as?: "link" | "button";
  className?: string;
}) {
  const inner = (
    <div
      className={clsx(
        "tick flex items-center gap-3 border border-ink/12 p-3.5 transition-colors duration-150",
        selected
          ? "tick-on bg-ink text-bone"
          : "bg-paper hover:tick-on hover:bg-bone-2",
        className,
      )}
    >
      <Flag name={name} />
      <div className="min-w-0 flex-1">
        <div className="display truncate text-lg leading-none">{name}</div>
        <div className="mt-1">
          <CountryCode name={name} />
        </div>
      </div>
      {position ? (
        <span className="display text-lg tnum opacity-50">{String(position).padStart(2, "0")}</span>
      ) : null}
    </div>
  );

  if (as === "button") {
    return (
      <button type="button" onClick={onClick} className="block w-full text-left">
        {inner}
      </button>
    );
  }
  return (
    <Link href={`/team/${teamSlug(name)}`} className="block">
      {inner}
    </Link>
  );
}
