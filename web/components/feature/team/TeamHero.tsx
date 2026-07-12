import { Flag } from "@/components/ui/Flag";
import { ConfidenceSignal } from "@/components/ui/Badge";
import { StatTile } from "@/components/ui/StatTile";
import type { TeamDetail } from "@/lib/api";
import { elo, confWords } from "@/lib/format";

function ordinal(n: number) {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return n + (s[(v - 20) % 10] || s[v] || s[0]);
}

export function TeamHero({ team }: { team: TeamDetail }) {
  const lead =
    team.position === 1
      ? `${team.team} field the strongest roster in the ENC 2026 field.`
      : team.position <= 4
        ? `${team.team} sit in the top tier — the ${ordinal(team.position)} strongest roster of sixteen.`
        : `${team.team} rank ${ordinal(team.position)} of sixteen on current roster form.`;

  return (
    <div>
      <div className="flex items-center gap-3">
        <span className="h-3 w-6 bg-red" />
        <span className="label text-ink-2">Seed #{team.position} · ENC 2026</span>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-3">
        <Flag name={team.team} size="lg" />
        <h1 className="display text-6xl text-ink sm:text-7xl">{team.team}</h1>
      </div>

      <p className="mt-5 max-w-2xl text-lg leading-relaxed text-ink-2">{lead}</p>

      <div className="mt-10 grid max-w-2xl grid-cols-2 gap-x-10 gap-y-6 sm:grid-cols-3">
        <StatTile
          label="Board rank"
          value={`#${team.position}`}
          sub="of 16 nations"
          emphasis={team.position === 1}
        />
        <StatTile
          label="Roster strength"
          value={team.roster_elo ? elo(team.roster_elo) : "—"}
          sub="Elo from recent club form"
        />
        <div className="border-t-2 border-ink pt-3">
          <div className="label text-ink-3">Confidence</div>
          <div className="mt-2">
            <ConfidenceSignal confidence={team.confidence} />
          </div>
          <div className="mt-2 text-xs leading-snug text-ink-3">{confWords(team.confidence)}</div>
        </div>
      </div>
    </div>
  );
}
