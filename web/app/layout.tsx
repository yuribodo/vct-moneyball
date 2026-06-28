import type { Metadata } from "next";
import { Oswald, Archivo } from "next/font/google";
import "./globals.css";
import { SiteHeader } from "@/components/layout/SiteHeader";
import { SiteFooter } from "@/components/layout/SiteFooter";
import { MotionProvider } from "@/components/motion/MotionProvider";

const display = Oswald({
  subsets: ["latin"],
  variable: "--font-oswald",
  weight: ["400", "500", "600", "700"],
});

const body = Archivo({
  subsets: ["latin"],
  variable: "--font-archivo",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Moneyball — ENC 2026 Power Index & Match Engine",
  description:
    "A locked, data-driven power ranking, head-to-head simulator, and bracket forecast for the 16 ENC 2026 national Valorant teams.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${display.variable} ${body.variable}`}>
      <body className="min-h-screen">
        <MotionProvider>
          <SiteHeader />
          <main className="mx-auto max-w-[68rem] px-5 sm:px-8">{children}</main>
          <SiteFooter />
        </MotionProvider>
      </body>
    </html>
  );
}
