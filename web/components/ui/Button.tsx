import Link from "next/link";
import { clsx } from "@/lib/clsx";

const base =
  "inline-flex items-center justify-center gap-2 px-6 py-3 display text-sm transition-colors duration-150 disabled:cursor-not-allowed disabled:opacity-40";

const variants = {
  primary: "cut bg-red text-bone hover:bg-red-deep",
  solid: "cut bg-ink text-bone hover:bg-ink-2",
  ghost: "border border-ink/25 text-ink hover:bg-ink hover:text-bone",
} as const;

type Variant = keyof typeof variants;

export function Button({
  variant = "primary",
  className,
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button className={clsx(base, variants[variant], className)} {...rest} />;
}

export function ButtonLink({
  variant = "primary",
  className,
  href,
  children,
}: {
  variant?: Variant;
  className?: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <Link href={href} className={clsx(base, variants[variant], className)}>
      {children}
    </Link>
  );
}
