import { clsx } from "@/lib/clsx";

type PanelProps = React.HTMLAttributes<HTMLDivElement> & {
  cut?: boolean;
  tone?: "paper" | "bone";
};

// A plain bordered surface. Used only where content genuinely needs a frame —
// not as decoration. No blur, no shadow, no glow.
export function Panel({ cut = false, tone = "paper", className, children, ...rest }: PanelProps) {
  return (
    <div
      className={clsx(
        tone === "paper" ? "bg-paper" : "bg-bone-2",
        "border border-ink/12",
        cut && "cut",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
