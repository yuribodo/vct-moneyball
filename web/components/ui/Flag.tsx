import { flagEmoji, shortCode } from "@/lib/countries";

export function Flag({ name, size = "md" }: { name: string; size?: "sm" | "md" | "lg" }) {
  const cls = size === "lg" ? "text-4xl" : size === "sm" ? "text-base" : "text-2xl";
  return (
    <span className={`${cls} leading-none`} role="img" aria-label={name}>
      {flagEmoji(name)}
    </span>
  );
}

export function CountryCode({ name }: { name: string }) {
  return <span className="label !tracking-[0.2em] text-ink-3">{shortCode(name)}</span>;
}
