"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AuditLogOut, AvailabilityWithPlayer, LineupOut, MatchOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDate, StatusBadge } from "@/components/StatusBadge";
import { AuditLogList } from "@/components/AuditLogList";

export default function CaptainMatchDetailPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const params = useParams<{ matchId: string }>();
  const matchId = Number(params.matchId);

  const [match, setMatch] = useState<MatchOut | null>(null);
  const [availability, setAvailability] = useState<AvailabilityWithPlayer[]>([]);
  const [lineup, setLineup] = useState<LineupOut | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [history, setHistory] = useState<AuditLogOut[]>([]);
  const [fetching, setFetching] = useState(true);
  const [publishing, setPublishing] = useState(false);

  const load = useCallback(async () => {
    setFetching(true);
    const [matchData, availabilityData, lineupData, historyData] = await Promise.all([
      api.get<MatchOut>(`/matches/${matchId}`),
      api.get<AvailabilityWithPlayer[]>(`/availability/match/${matchId}`),
      api.get<LineupOut>(`/lineups/match/${matchId}`),
      api.get<AuditLogOut[]>(`/audit-log/match/${matchId}`),
    ]);
    setMatch(matchData);
    setAvailability(availabilityData.sort((a, b) => a.player_naam.localeCompare(b.player_naam)));
    setLineup(lineupData);
    setSelected(new Set(lineupData.player_ids));
    setHistory(historyData);
    setFetching(false);
  }, [matchId]);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.rol !== "CAPTAIN" && user.rol !== "BEHEER") {
      router.replace("/speler");
      return;
    }
    load();
  }, [user, loading, router, load]);

  function toggle(playerId: number) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(playerId)) next.delete(playerId);
      else next.add(playerId);
      return next;
    });
  }

  async function refreshHistory() {
    const h = await api.get<AuditLogOut[]>(`/audit-log/match/${matchId}`);
    setHistory(h);
  }

  async function saveLineup() {
    const updated = await api.put<LineupOut>(`/lineups/match/${matchId}`, {
      player_ids: Array.from(selected),
    });
    setLineup(updated);
    await refreshHistory();
  }

  async function publish() {
    setPublishing(true);
    try {
      await saveLineup();
      const published = await api.post<LineupOut>(`/lineups/match/${matchId}/publish`);
      setLineup(published);
      await refreshHistory();
    } finally {
      setPublishing(false);
    }
  }

  if (loading || fetching || !match) {
    return <div className="py-10 text-center text-gray-400">Laden...</div>;
  }

  const beschikbaarAantal = availability.filter((a) => a.status === "AVAILABLE").length;

  return (
    <div>
      <Nav />
      <h1 className="mb-1 text-xl font-bold capitalize">{formatMatchDate(match.datum)}</h1>
      <p className="mb-6 text-gray-500">
        {match.thuisteam} – {match.uitteam}
        {match.locatie && ` · 📍 ${match.locatie}`}
      </p>

      <h2 className="mb-3 font-medium">Beschikbaarheid</h2>
      <table className="mb-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white text-sm">
        <thead className="bg-gray-50 text-left text-gray-500">
          <tr>
            <th className="px-4 py-2 font-medium">Speler</th>
            <th className="px-4 py-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {availability.map((a) => (
            <tr key={a.id}>
              <td className="px-4 py-2">{a.player_naam}</td>
              <td className="px-4 py-2">
                <StatusBadge status={a.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mb-6 text-sm text-gray-500">{beschikbaarAantal} spelers beschikbaar</p>

      <h2 className="mb-3 font-medium">Opstelling</h2>
      <div className="mb-2 divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white">
        {availability
          .filter((a) => a.status !== "UNAVAILABLE")
          .map((a) => (
            <label key={a.player_id} className="flex items-center gap-3 px-4 py-3 text-sm">
              <input
                type="checkbox"
                checked={selected.has(a.player_id)}
                onChange={() => toggle(a.player_id)}
                className="h-4 w-4"
              />
              {a.player_naam}
            </label>
          ))}
      </div>
      <p className="mb-6 text-sm text-gray-500">{selected.size} / 4 opgesteld</p>

      <div className="flex gap-3">
        <button
          onClick={saveLineup}
          className="flex-1 rounded-lg border border-gray-300 py-2 font-medium text-gray-700 hover:bg-gray-50"
        >
          Opslaan
        </button>
        <button
          onClick={publish}
          disabled={publishing}
          className="flex-1 rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {lineup?.published ? "Opnieuw publiceren" : "Opstelling publiceren"}
        </button>
      </div>
      {lineup?.published && (
        <p className="mt-3 text-sm text-green-700">✅ Opstelling is gepubliceerd naar spelers</p>
      )}

      <details className="mt-8">
        <summary className="cursor-pointer font-medium text-gray-700">
          Geschiedenis {history.length > 0 && `(${history.length})`}
        </summary>
        <div className="mt-3">
          <AuditLogList entries={history} />
        </div>
      </details>
    </div>
  );
}
