"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clsx } from "@/lib/clsx";

const NAV = [
  { href: "/rankings", label: "Rankings" },
  { href: "/simulate", label: "Simulate" },
  { href: "/bracket", label: "Bracket" },
  { href: "/honesty", label: "The Model" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 border-b border-ink/15 bg-bone/85 backdrop-blur-[2px]">
      <div className="mx-auto flex max-w-[68rem] items-center justify-between px-5 py-3 sm:px-8">
        <Link href="/" className="flex items-center gap-2.5">
          <span className="cut flex h-7 w-7 items-center justify-center bg-red">
            <span className="display text-base leading-none text-bone">M</span>
          </span>
          <span className="display text-xl leading-none text-ink">
            Moneyball
          </span>
          <span className="label hidden text-ink-3 sm:inline">ENC&nbsp;2026</span>
        </Link>

        <nav className="flex items-center" aria-label="Sections">
          {NAV.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "display relative px-3 py-2 text-sm transition-colors sm:px-4",
                  active ? "text-ink" : "text-ink-3 hover:text-ink",
                )}
              >
                {item.label}
                {active ? <span className="absolute inset-x-3 -bottom-px h-0.5 bg-red sm:inset-x-4" /> : null}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
