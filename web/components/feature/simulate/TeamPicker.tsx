"use client";

import { useState } from "react";
import { Flag, CountryCode } from "@/components/ui/Flag";
import { clsx } from "@/lib/clsx";

export function TeamPicker({
  teams,
  disabled,
  onPick,
  onClose,
}: {
  teams: string[];
  disabled?: string;
  onPick: (team: string) => void;
  onClose: () => void;
}) {
  const [q, setQ] = useState("");
  const filtered = teams.filter((t) => t.toLowerCase().includes(q.toLowerCase()));

  return (
    <div className="mt-4 border border-ink/20 bg-paper p-4">
      <div className="mb-3 flex items-center gap-3">
        <input
          autoFocus
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search nations…"
          className="flex-1 border border-ink/20 bg-bone px-3 py-2 text-sm text-ink outline-none focus:border-red"
        />
        <button onClick={onClose} className="label border border-ink/20 px-3 py-2 text-ink-2 hover:bg-bone-2">
          Close
        </button>
      </div>
      <div className="grid max-h-72 grid-cols-2 gap-px overflow-y-auto bg-ink/10 sm:grid-cols-3">
        {filtered.map((t) => {
          const isDisabled = t === disabled;
          return (
            <button
              key={t}
              disabled={isDisabled}
              onClick={() => onPick(t)}
              className={clsx(
                "flex items-center gap-2.5 bg-bone p-2.5 text-left transition-colors",
                isDisabled ? "cursor-not-allowed opacity-30" : "hover:bg-bone-2",
              )}
            >
              <Flag name={t} size="sm" />
              <div className="min-w-0">
                <div className="truncate text-sm font-medium text-ink">{t}</div>
                <CountryCode name={t} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
