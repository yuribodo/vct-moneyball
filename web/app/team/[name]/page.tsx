import { notFound } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { TeamHero } from "@/components/feature/team/TeamHero";
import { RosterGrid } from "@/components/feature/team/RosterGrid";
import { MapRadar } from "@/components/charts/MapRadar";
import { ProvenanceLine } from "@/components/ui/ProvenanceLine";
import { EmptyState } from "@/components/ui/States";
import { ButtonLink } from "@/components/ui/Button";
import { teamFromSlug } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function TeamPage({ params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  const teamName = teamFromSlug(name);

  let team;
  try {
    team = await api.team(teamName);
  } catch (e) {
    const err = e as ApiError;
    if (err.status === 404) notFound();
    return (
      <div className="py-20">
        <EmptyState kicker="Unavailable" title="Couldn't load this team">
          {err.message}
        </EmptyState>
      </div>
    );
  }

  const byScore = [...team.map_breakdown].sort((a, b) => b.map_score - a.map_score);
  const best = byScore[0];
  const worst = byScore[byScore.length - 1];

  return (
    <div className="py-12 sm:py-16">
      <TeamHero team={team} />

      <div className="mt-16 grid gap-14 lg:grid-cols-[1.05fr_1fr]">
        <section>
          <div className="mb-1 flex items-baseline justify-between border-b border-ink/15 pb-2">
            <h2 className="display text-2xl text-ink">Who&apos;s carrying</h2>
            <span className="label text-ink-3">Player rating · club maps</span>
          </div>
          <RosterGrid contributors={team.contributors} />
          <p className="mt-3 text-sm text-ink-3">
            Each player&apos;s rating is their individual strength from recent club maps — the
            roster Elo above is built from these.
          </p>
        </section>

        <section>
          <div className="mb-4 flex items-baseline justify-between border-b border-ink/15 pb-2">
            <h2 className="display text-2xl text-ink">Map strength</h2>
            <span className="label text-ink-3">12-map pool</span>
          </div>
          <MapRadar maps={team.map_breakdown} />
          {best && worst ? (
            <div className="mt-6 grid grid-cols-2 gap-px bg-ink/15">
              <div className="bg-bone px-4 py-3">
                <div className="label text-red">Strongest</div>
                <div className="display mt-1 text-xl text-ink">{best.map}</div>
                <div className="text-xs text-ink-3">rated {best.map_score.toFixed(3)}</div>
              </div>
              <div className="bg-bone px-4 py-3">
                <div className="label text-ink-3">Softest</div>
                <div className="display mt-1 text-xl text-ink">{worst.map}</div>
                <div className="text-xs text-ink-3">rated {worst.map_score.toFixed(3)}</div>
              </div>
            </div>
          ) : null}
        </section>
      </div>

      <div className="mt-12 flex flex-wrap gap-3">
        <ButtonLink href={`/simulate?a=${encodeURIComponent(team.team)}`}>
          Simulate a match
        </ButtonLink>
        <ButtonLink href="/rankings" variant="ghost">
          Back to the board
        </ButtonLink>
      </div>

      <ProvenanceLine p={team.provenance} />
    </div>
  );
}
