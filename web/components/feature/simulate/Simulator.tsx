"use client";

import { useEffect, useState } from "react";
import { api, ApiError, type Prediction } from "@/lib/api";
import { TeamPicker } from "./TeamPicker";
import { VersusReveal } from "./VersusReveal";
import { Button } from "@/components/ui/Button";
import { Flag, CountryCode } from "@/components/ui/Flag";
import { clsx } from "@/lib/clsx";

type Slot = "a" | "b" | null;

function SlotButton({
  team,
  label,
  active,
  onClick,
}: {
  team: string | null;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "cut flex h-32 w-full flex-col items-center justify-center gap-2 border p-4 transition-colors duration-150",
        active
          ? "border-red bg-bone-2"
          : team
            ? "border-ink/20 bg-paper hover:bg-bone-2"
            : "border-dashed border-ink/30 bg-paper hover:bg-bone-2",
      )}
    >
      <span className="label text-ink-3">{label}</span>
      {team ? (
        <>
          <Flag name={team} />
          <span className="display text-lg leading-none text-ink">{team}</span>
          <CountryCode name={team} />
        </>
      ) : (
        <span className="display text-lg text-ink-3">Pick a nation</span>
      )}
    </button>
  );
}

export function Simulator({ initialA, initialB }: { initialA?: string; initialB?: string }) {
  const [teams, setTeams] = useState<string[]>([]);
  const [teamA, setTeamA] = useState<string | null>(initialA ?? null);
  const [teamB, setTeamB] = useState<string | null>(initialB ?? null);
  const [asOf, setAsOf] = useState("2026-11-08");
  const [picking, setPicking] = useState<Slot>(null);
  const [result, setResult] = useState<Prediction | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api
      .ranking()
      .then((r) => setTeams(r.teams.map((t) => t.team)))
      .catch((e: ApiError) => setError(e.message));
  }, []);

  async function simulate() {
    if (!teamA || !teamB) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await api.predict(teamA, teamB, asOf));
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setLoading(false);
    }
  }

  function pick(team: string) {
    if (picking === "a") setTeamA(team);
    if (picking === "b") setTeamB(team);
    setPicking(null);
  }

  const ready = teamA && teamB && teamA !== teamB;

  return (
    <div>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-4 sm:gap-6">
        <SlotButton team={teamA} label="Home" active={picking === "a"} onClick={() => setPicking(picking === "a" ? null : "a")} />
        <span className="display text-3xl text-red">VS</span>
        <SlotButton team={teamB} label="Away" active={picking === "b"} onClick={() => setPicking(picking === "b" ? null : "b")} />
      </div>

      {picking ? (
        <TeamPicker
          teams={teams}
          disabled={picking === "a" ? teamB ?? undefined : teamA ?? undefined}
          onPick={pick}
          onClose={() => setPicking(null)}
        />
      ) : null}

      <div className="mt-6 flex flex-wrap items-end justify-between gap-4">
        <label className="text-sm">
          <span className="label mb-1.5 block text-ink-3">Forecast as of</span>
          <input
            type="date"
            value={asOf}
            onChange={(e) => setAsOf(e.target.value)}
            className="border border-ink/25 bg-paper px-3 py-2 text-sm text-ink outline-none focus:border-red"
          />
        </label>
        <Button onClick={simulate} disabled={!ready || loading}>
          {loading ? "Running the tape…" : "Simulate match"}
        </Button>
      </div>

      {error ? (
        <p className="mt-6 border-l-2 border-red bg-bone-2 px-4 py-3 text-sm text-ink-2">{error}</p>
      ) : null}

      {result ? <VersusReveal result={result} /> : null}
    </div>
  );
}
