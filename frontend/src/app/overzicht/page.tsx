"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AvailabilityWithPlayer, LineupOut, MatchOut, SeasonOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDateShort, StatusDot } from "@/components/StatusBadge";

interface PlayerColumn {
  id: number;
  naam: string;
}

export default function OverzichtPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [availability, setAvailability] = useState<AvailabilityWithPlayer[]>([]);
  const [lineups, setLineups] = useState<Map<number, Set<number>>>(new Map());
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [seasonFilter, setSeasonFilter] = useState("");
  const [upcomingOnly, setUpcomingOnly] = useState(true);
  const [fetching, setFetching] = useState(true);
  const [landscapeLocked, setLandscapeLocked] = useState(false);
  const [showLandscapeToggle, setShowLandscapeToggle] = useState(false);
  const [landscapeError, setLandscapeError] = useState<string | null>(null);

  // "Liggend weergeven" is alleen zinvol op een smal (telefoon/kleine
  // tablet) scherm — op desktop is er toch al genoeg breedte.
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 768px)");
    setShowLandscapeToggle(mq.matches);
    const handler = (e: MediaQueryListEvent) => setShowLandscapeToggle(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  // Verlaat de gebruiker fullscreen op een andere manier dan onze eigen
  // knop (terugknop, systeem-gebaar), dan moet de knoptekst dat volgen —
  // anders staat er "Normaal weergeven" terwijl je alweer terug bent.
  useEffect(() => {
    function handleFullscreenChange() {
      if (!document.fullscreenElement) setLandscapeLocked(false);
    }
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  async function toggleLandscape() {
    setLandscapeError(null);
    const orientation = screen.orientation as ScreenOrientation & {
      lock?: (o: string) => Promise<void>;
    };
    if (!landscapeLocked) {
      try {
        if (document.documentElement.requestFullscreen) {
          await document.documentElement.requestFullscreen();
        }
        if (!orientation?.lock) throw new Error("orientation lock niet ondersteund");
        await orientation.lock("landscape");
        setLandscapeLocked(true);
      } catch {
        setLandscapeError(
          "Liggend vastzetten wordt niet ondersteund op dit toestel/deze browser — draai je toestel handmatig, de tabel past zich al automatisch aan."
        );
        if (document.fullscreenElement) {
          await document.exitFullscreen().catch(() => {});
        }
      }
    } else {
      orientation?.unlock?.();
      if (document.fullscreenElement) {
        await document.exitFullscreen().catch(() => {});
      }
      setLandscapeLocked(false);
    }
  }

  const load = useCallback(async (seasonId: string, upcoming: boolean) => {
    const params = new URLSearchParams();
    if (seasonId) params.set("season_id", seasonId);
    if (upcoming) params.set("upcoming_only", "true");
    const query = params.toString() ? `?${params.toString()}` : "";
    const [matchesData, availabilityData] = await Promise.all([
      api.get<MatchOut[]>(`/matches${query}`),
      api.get<AvailabilityWithPlayer[]>(`/availability/overview${query}`),
    ]);
    const sortedMatches = [...matchesData].sort((a, b) => a.datum.localeCompare(b.datum));
    setMatches(sortedMatches);
    setAvailability(availabilityData);

    const lineupResults = await Promise.all(
      sortedMatches.map((match) =>
        api.get<LineupOut>(`/lineups/match/${match.id}`).catch(() => null)
      )
    );
    const lineupMap = new Map<number, Set<number>>();
    lineupResults.forEach((result) => {
      if (result && result.published) lineupMap.set(result.match_id, new Set(result.player_ids));
    });
    setLineups(lineupMap);
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    api
      .get<SeasonOut[]>("/seasons")
      .then(async (seasonsData) => {
        setSeasons(seasonsData);
        const active = seasonsData.find((s) => s.actief);
        const initial = active ? String(active.id) : "";
        setSeasonFilter(initial);
        await load(initial, true);
      })
      .finally(() => setFetching(false));
  }, [user, loading, router, load]);

  async function handleSeasonChange(value: string) {
    setSeasonFilter(value);
    await load(value, upcomingOnly);
  }

  async function handleUpcomingToggle(value: boolean) {
    setUpcomingOnly(value);
    await load(seasonFilter, value);
  }

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  const players: PlayerColumn[] = Array.from(
    new Map(availability.map((a) => [a.player_id, { id: a.player_id, naam: a.player_naam }])).values()
  ).sort((a, b) => a.naam.localeCompare(b.naam));

  const byMatchAndPlayer = new Map(availability.map((a) => [`${a.match_id}-${a.player_id}`, a]));

  const body = (
    <>
      <Nav />
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-bold">Overzicht</h1>
        {showLandscapeToggle && (
          <button
            onClick={toggleLandscape}
            className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            {landscapeLocked ? "📱 Normaal weergeven" : "📱⟳ Liggend weergeven"}
          </button>
        )}
      </div>
      {landscapeError && <p className="mb-2 text-sm text-red-600">{landscapeError}</p>}
      <p className="mb-4 text-gray-500">
        Wie kan wanneer wel of niet — handig om samen een ruil te regelen. Alleen-lezen: wijzigen doe
        je nog steeds bij jezelf op je eigen scherm.
      </p>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <select
          value={seasonFilter}
          onChange={(e) => handleSeasonChange(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
        >
          <option value="">Alle seizoenen</option>
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.naam}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={upcomingOnly}
            onChange={(e) => handleUpcomingToggle(e.target.checked)}
          />
          Alleen komende wedstrijden
        </label>
      </div>

      <p className="mb-3 text-xs text-gray-500">
        🟢 Kan &nbsp;·&nbsp; 🔴 Kan niet &nbsp;·&nbsp; 🟡 Indien nodig &nbsp;·&nbsp; ⚪ Geen antwoord
        &nbsp;·&nbsp; ⭐ Opgesteld
      </p>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500">
            <tr>
              <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-left font-medium">
                Wedstrijd
              </th>
              {players.map((p) => (
                <th key={p.id} className="px-2 py-2 text-center font-medium" title={p.naam}>
                  {p.naam.split(" ")[0]}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {matches.map((match) => (
              <tr key={match.id}>
                <td className="sticky left-0 z-10 whitespace-nowrap bg-white px-3 py-2">
                  <span className="text-gray-500">{formatMatchDateShort(match.datum)}</span>{" "}
                  {match.thuisteam} - {match.uitteam}
                </td>
                {players.map((p) => {
                  const a = byMatchAndPlayer.get(`${match.id}-${p.id}`);
                  const opgesteld = lineups.get(match.id)?.has(p.id) ?? false;
                  return (
                    <td key={p.id} className="whitespace-nowrap px-2 py-2 text-center">
                      <StatusDot status={a?.status ?? "NO_RESPONSE"} />
                      {opgesteld && <span title="Opgesteld">⭐</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
            {matches.length === 0 && (
              <tr>
                <td colSpan={players.length + 1} className="px-3 py-6 text-center text-gray-400">
                  Geen wedstrijden gevonden
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );

  return (
    // Doorbreekt bewust de max-w-2xl van het layout-frame: dit is de enige
    // pagina met een brede tabel (wedstrijd × elke speler), en op een
    // liggend scherm (tablet/telefoon) blijft die anders onnodig smal
    // terwijl er zichtbaar ruimte over is — zie ook overflow-x-auto
    // hieronder als vangnet voor als het echt niet past.
    <div className="relative left-1/2 right-1/2 -mx-[50vw] w-screen px-4 sm:px-6">
      <div className="mx-auto max-w-screen-2xl">{body}</div>
    </div>
  );
}
