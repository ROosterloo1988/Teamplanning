"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { LineupOut, MatchOut, SeasonOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDate, LocatieLink } from "@/components/StatusBadge";

export default function GeschiedenisPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [seasonFilter, setSeasonFilter] = useState("");
  const [fetching, setFetching] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [lineups, setLineups] = useState<Record<number, LineupOut>>({});

  const loadMatches = useCallback(async (seasonId: string) => {
    const query = seasonId ? `?season_id=${seasonId}` : "";
    const data = await api.get<MatchOut[]>(`/matches${query}`);
    const today = new Date().toISOString().slice(0, 10);
    const past = data.filter((m) => m.datum < today).sort((a, b) => b.datum.localeCompare(a.datum));
    setMatches(past);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    Promise.all([loadMatches(""), api.get<SeasonOut[]>("/seasons")])
      .then(([, seasonsData]) => setSeasons(seasonsData))
      .finally(() => setFetching(false));
  }, [user, loading, router, loadMatches]);

  async function handleFilterChange(value: string) {
    setSeasonFilter(value);
    await loadMatches(value);
  }

  async function toggleExpand(matchId: number) {
    if (expanded === matchId) {
      setExpanded(null);
      return;
    }
    setExpanded(matchId);
    if (!lineups[matchId]) {
      const lineup = await api.get<LineupOut>(`/lineups/match/${matchId}`);
      setLineups((prev) => ({ ...prev, [matchId]: lineup }));
    }
  }

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Wedstrijdhistorie</h1>
        <select
          value={seasonFilter}
          onChange={(e) => handleFilterChange(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">Alle seizoenen</option>
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.naam}
            </option>
          ))}
        </select>
      </div>
      <p className="mb-6 text-gray-500">Afgelopen wedstrijden met de gepubliceerde opstelling.</p>

      <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {matches.map((match) => {
          const lineup = lineups[match.id];
          return (
            <li key={match.id}>
              <button
                onClick={() => toggleExpand(match.id)}
                className="flex w-full flex-col gap-1 px-4 py-3 text-left hover:bg-gray-50"
              >
                <span className="text-sm text-gray-500 capitalize">{formatMatchDate(match.datum)}</span>
                <span className="font-medium">
                  {match.thuisteam} - {match.uitteam}
                </span>
              </button>
              {expanded === match.id && (
                <div className="space-y-2 border-t border-gray-100 bg-gray-50 px-4 py-3 text-sm">
                  {match.locatie && <LocatieLink locatie={match.locatie} />}
                  {!lineup && <p className="text-gray-400">Laden...</p>}
                  {lineup && lineup.published && lineup.player_naam.length > 0 && (
                    <p>
                      <span className="text-gray-500">Opgesteld: </span>
                      {lineup.player_naam.join(", ")}
                    </p>
                  )}
                  {lineup && (!lineup.published || lineup.player_naam.length === 0) && (
                    <p className="text-gray-400">Geen opstelling gepubliceerd.</p>
                  )}
                  {user && (user.rol === "CAPTAIN" || user.rol === "BEHEER") && (
                    <Link href={`/captain/${match.id}`} className="inline-block text-brand hover:underline">
                      Opstelling aanpassen →
                    </Link>
                  )}
                </div>
              )}
            </li>
          );
        })}
        {matches.length === 0 && (
          <li className="px-4 py-6 text-center text-gray-400">Geen afgelopen wedstrijden</li>
        )}
      </ul>
    </div>
  );
}
