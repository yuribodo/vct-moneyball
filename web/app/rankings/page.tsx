import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { RankingList } from "@/components/feature/rankings/RankingList";
import { ProvenanceLine } from "@/components/ui/ProvenanceLine";
import { EmptyState } from "@/components/ui/States";
import { SectionHeading } from "@/components/ui/GlowDivider";
import { clsx } from "@/lib/clsx";

export const dynamic = "force-dynamic";

export default async function RankingsPage({
  searchParams,
}: {
  searchParams: Promise<{ source?: string }>;
}) {
  const { source: rawSource } = await searchParams;
  const source = rawSource === "power" ? "power" : "roster";

  let teams;
  let provenance;
  try {
    const r = await api.ranking(source);
    teams = r.teams;
    provenance = r.provenance;
  } catch (e) {
    return (
      <div className="py-20">
        <EmptyState kicker="Ranking unavailable" title="The board isn't published yet">
          {(e as ApiError).message}
        </EmptyState>
      </div>
    );
  }

  return (
    <div className="py-12 sm:py-16">
      <SectionHeading kicker="Power Index" title="The Board">
        {source === "roster"
          ? "Each nation rated by the strength of its active roster — an Elo from recent club form, weighted so big international events and dominant wins count for more. The field is tight: outside the front-runners, many teams are near coin-flips, so read the tiers, not the exact rank."
          : "Each nation's raw squad score from feature-001 power ranking. Tap a nation for the full breakdown."}
      </SectionHeading>

      <div className="mb-8 flex flex-wrap items-center gap-6">
        <div className="inline-flex border border-ink/20">
          {(["roster", "power"] as const).map((s) => (
            <Link
              key={s}
              href={`/rankings?source=${s}`}
              className={clsx(
                "display px-4 py-2 text-sm transition-colors",
                source === s ? "bg-ink text-bone" : "text-ink-3 hover:text-ink",
              )}
            >
              {s === "roster" ? "Roster Elo" : "Power Score"}
            </Link>
          ))}
        </div>
        <p className="max-w-md text-sm text-ink-3">
          The <span className="text-ink-2">Data</span> column shows how much club history backs each
          rating — three bars is a deep sample, one means read with caution. It measures data
          volume, not how tough the opposition was.
        </p>
      </div>

      <RankingList teams={teams} source={source} />
      {provenance ? <ProvenanceLine p={provenance} /> : null}
    </div>
  );
}
