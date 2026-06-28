import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "VCT Moneyball — ENC 2026",
  description: "Data-driven power ranking and match predictions for the ENC 2026 cohort.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="site-header">
          <div className="wrap header-inner">
            <Link href="/" className="brand">
              VCT <span>Moneyball</span>
            </Link>
            <nav className="nav">
              <Link href="/">Ranking</Link>
              <Link href="/predict">Predict</Link>
              <Link href="/honesty">Honesty</Link>
            </nav>
          </div>
        </header>
        <main className="wrap">{children}</main>
        <footer className="site-footer wrap">
          <span>
            ENC 2026 — predictions locked before kickoff. When it&apos;s over, the data shows
            who was right.
          </span>
        </footer>
      </body>
    </html>
  );
}
