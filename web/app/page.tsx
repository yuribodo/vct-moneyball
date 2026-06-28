import Link from "next/link";
import { api } from "@/lib/api";
import { Hero } from "@/components/feature/home/Hero";
import { TopFive } from "@/components/feature/home/TopFive";
import { ButtonLink } from "@/components/ui/Button";

export const dynamic = "force-dynamic";

const FEATURES = [
  {
    href: "/rankings",
    n: "01",
    title: "The Board",
    body: "All sixteen nations ranked by live roster strength, with the data depth behind each rating.",
  },
  {
    href: "/simulate",
    n: "02",
    title: "Match Simulator",
    body: "Pick two nations and a date. Get a calibrated win chance and the players who decide it.",
  },
  {
    href: "/bracket",
    n: "03",
    title: "Bracket Engine",
    body: "Seed the field and run it to a champion — plus title odds across 2,000 simulations.",
  },
];

export default async function HomePage() {
  let top5: Awaited<ReturnType<typeof api.ranking>>["teams"] = [];
  try {
    const r = await api.ranking("roster");
    top5 = r.teams.slice(0, 5);
  } catch {
    /* hero still renders without the teaser */
  }

  return (
    <div className="pb-12">
      <Hero />

      <div className="mt-24 grid gap-14 lg:grid-cols-[1fr_1.15fr] lg:items-start">
        {top5.length ? (
          <section>
            <div className="mb-1 flex items-baseline justify-between border-b border-ink/15 pb-2">
              <h2 className="display text-2xl text-ink">Top of the board</h2>
              <Link href="/rankings" className="label text-red hover:underline">
                Full ranking
              </Link>
            </div>
            <TopFive teams={top5} />
          </section>
        ) : null}

        <section>
          {FEATURES.map((f) => (
            <Link
              key={f.href}
              href={f.href}
              className="tick group flex items-start gap-5 border-b border-ink/12 py-6 transition-colors duration-150 hover:tick-on hover:bg-bone-2"
            >
              <span className="display text-3xl tnum text-ink-3 group-hover:text-red">{f.n}</span>
              <div>
                <h3 className="display text-2xl text-ink">{f.title}</h3>
                <p className="mt-1.5 max-w-md text-ink-2">{f.body}</p>
              </div>
              <span className="display ml-auto text-2xl text-ink-3 transition-transform duration-150 group-hover:translate-x-1 group-hover:text-red">
                →
              </span>
            </Link>
          ))}
        </section>
      </div>

      <section className="mt-24 border-t-2 border-ink pt-10">
        <p className="display max-w-3xl text-3xl leading-tight text-ink sm:text-4xl">
          Predictions dated and frozen before a single map is played.
        </p>
        <p className="mt-4 max-w-xl text-ink-2">
          When the tournament ends, the data shows who was right — not the loudest take.
        </p>
        <div className="mt-6">
          <ButtonLink href="/honesty" variant="ghost">
            See how the model is scored
          </ButtonLink>
        </div>
      </section>
    </div>
  );
}
