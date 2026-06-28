import type { Metadata } from "next";
import { Archivo, Fraunces } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  axes: ["SOFT", "WONK", "opsz"],
  style: ["normal", "italic"],
});

const text = Archivo({
  subsets: ["latin"],
  variable: "--font-text",
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "The Moneyball Ledger — ENC 2026",
  description:
    "A locked, data-driven power ranking and match forecast for the 16 ENC 2026 national teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${text.variable}`}>
      <body>
        <div className="dateline">
          <span>VCT&nbsp;Moneyball</span>
          <span className="stamp">Predictions Locked · 28 Jun 2026</span>
          <span className="tabular">Vol. I — ENC&nbsp;2026</span>
        </div>

        <header className="masthead">
          <Link href="/" className="wordmark">
            The Moneyball <em>Ledger</em>
          </Link>
          <p className="masthead-sub">
            Sixteen nations. One number each. Settled when it&apos;s over.
          </p>
          <nav className="ledger-nav" aria-label="Sections">
            <Link href="/">Power Ranking</Link>
            <Link href="/predict">Head&#8209;to&#8209;Head</Link>
            <Link href="/honesty">The Reckoning</Link>
          </nav>
        </header>

        <main>{children}</main>

        <footer className="colophon">
          <p>
            Every prediction here was dated and frozen before a single map was played. When
            the tournament ends, the data shows who was right — not the loudest take.
          </p>
          <p className="colophon-meta">
            Built from VLR.gg match data · leakage-checked · baseline-relative · reproducible
            from versioned inputs.
          </p>
        </footer>
      </body>
    </html>
  );
}
