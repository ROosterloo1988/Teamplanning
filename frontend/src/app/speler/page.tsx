"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AvailabilityOut, AvailabilityStatus, LineupOut, MatchOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { daysUntil, formatMatchDate, formatMatchDateShort, StatusBadge } from "@/components/StatusBadge";

// Zie functioneel ontwerp v1 sectie 11: herinnering vanaf N dagen voor de wedstrijd.
const REMINDER_DAYS_BEFORE = 3;

interface Row {
  match: MatchOut;
  availability: AvailabilityOut | null;
}

export default function SpelerPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [rows, setRows] = useState<Row[]>([]);
  const [lineup, setLineup] = useState<LineupOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [fetching, setFetching] = useState(true);

  const load = useCallback(async () => {
    setFetching(true);
    const [matches, availabilities] = await Promise.all([
      api.get<MatchOut[]>("/matches?upcoming_only=true"),
      api.get<AvailabilityOut[]>("/availability/me"),
    ]);
    const byMatch = new Map(availabilities.map((a) => [a.match_id, a]));
    const combined = matches
      .map((match) => ({ match, availability: byMatch.get(match.id) ?? null }))
      .sort((a, b) => a.match.datum.localeCompare(b.match.datum));
    setRows(combined);

    if (combined.length > 0) {
      try {
        const nextLineup = await api.get<LineupOut>(`/lineups/match/${combined[0].match.id}`);
        setLineup(nextLineup.published ? nextLineup : null);
      } catch {
        setLineup(null);
      }
    }
    setFetching(false);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load();
  }, [user, loading, router, load]);

  async function setStatus(matchId: number, status: AvailabilityStatus) {
    setBusy(true);
    try {
      const updated = await api.put<AvailabilityOut>(`/availability/${matchId}`, { status });
      setRows((prev) =>
        prev.map((row) => (row.match.id === matchId ? { ...row, availability: updated } : row))
      );
    } finally {
      setBusy(false);
    }
  }

  if (loading || fetching) {
    return <div className="py-10 text-center text-gray-400">🏓 Laden...</div>;
  }

  const next = rows[0];
  const upcoming = rows.slice(0, 8);
  const showReminder =
    !!next &&
    (next.availability?.status ?? "NO_RESPONSE") === "NO_RESPONSE" &&
    daysUntil(next.match.datum) <= REMINDER_DAYS_BEFORE &&
    daysUntil(next.match.datum) >= 0;

  return (
    <div>
      <Nav />
      <h1 className="mb-1 text-2xl font-bold">🏓 De Gouv</h1>
      <p className="mb-6 text-gray-500">Welkom {user?.naam}</p>

      {!next && <p className="text-gray-500">Geen aankomende wedstrijden gepland.</p>}

      {showReminder && (
        <div className="mb-4 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          🏓 Je hebt je beschikbaarheid voor{" "}
          <span className="font-medium">{formatMatchDate(next.match.datum)}</span> nog niet ingevuld.
        </div>
      )}

      {next && (
        <div className="mb-8 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="mb-2 text-sm font-medium uppercase tracking-wide text-gray-500">
            Eerstvolgende wedstrijd
          </h2>
          <p className="mb-3 text-lg font-semibold capitalize">{formatMatchDate(next.match.datum)}</p>
          <p className="text-xl font-bold">{next.match.thuisteam}</p>
          <p className="text-gray-400">tegen</p>
          <p className="text-xl font-bold">{next.match.uitteam}</p>
          {next.match.locatie && <p className="mt-2 text-gray-500">📍 {next.match.locatie}</p>}

          {lineup && (
            <div className="mt-4 rounded-lg bg-green-50 p-3 text-sm">
              <p className="mb-1 font-medium text-green-800">🏓 Opstelling bekend</p>
              <p className="text-green-700">
                {lineup.player_ids.length} speler{lineup.player_ids.length === 1 ? "" : "s"} opgesteld
              </p>
            </div>
          )}

          <h3 className="mb-3 mt-6 font-medium">Kun je spelen?</h3>
          <div className="space-y-2">
            <StatusChoiceButton
              label="🟢 JA, ik kan"
              active={next.availability?.status === "AVAILABLE"}
              disabled={busy}
              onClick={() => setStatus(next.match.id, "AVAILABLE")}
              color="green"
            />
            <StatusChoiceButton
              label="🔴 NEE, ik kan niet"
              active={next.availability?.status === "UNAVAILABLE"}
              disabled={busy}
              onClick={() => setStatus(next.match.id, "UNAVAILABLE")}
              color="red"
            />
            <StatusChoiceButton
              label="🟡 ALLEEN ALS HET NODIG IS"
              active={next.availability?.status === "IF_NEEDED"}
              disabled={busy}
              onClick={() => setStatus(next.match.id, "IF_NEEDED")}
              color="yellow"
            />
          </div>
        </div>
      )}

      <h3 className="mb-3 font-medium">Mijn komende wedstrijden</h3>
      <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {upcoming.map(({ match, availability }) => (
          <li key={match.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <span className="text-gray-500">{formatMatchDateShort(match.datum)}</span>
            <span>{match.thuisteam} - {match.uitteam}</span>
            <span>
              <StatusBadge status={availability?.status ?? "NO_RESPONSE"} />
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatusChoiceButton({
  label,
  active,
  disabled,
  onClick,
  color,
}: {
  label: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
  color: "green" | "red" | "yellow";
}) {
  const colorClasses = {
    green: active ? "bg-green-600 text-white border-green-600" : "border-green-300 text-green-700",
    red: active ? "bg-red-600 text-white border-red-600" : "border-red-300 text-red-700",
    yellow: active ? "bg-yellow-500 text-white border-yellow-500" : "border-yellow-300 text-yellow-700",
  }[color];

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full rounded-lg border-2 py-3 text-center font-semibold transition disabled:opacity-50 ${colorClasses}`}
    >
      {label}
    </button>
  );
}
