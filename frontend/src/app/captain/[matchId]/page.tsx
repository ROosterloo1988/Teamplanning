"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AuditLogOut, AvailabilityWithPlayer, LineupOut, MatchOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDate, LocatieLink, mapsUrl, StatusBadge } from "@/components/StatusBadge";
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
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");

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

  // Geen e-mail of andere verzending: de captain plakt dit zelf in de
  // WhatsApp-groep. Gebaseerd op de huidige selectie, niet pas na publiceren,
  // zodat er ook een concept-tekst gekopieerd kan worden.
  function buildWhatsAppText(): string {
    if (!match) return "";
    const spelers = availability
      .filter((a) => selected.has(a.player_id))
      .map((a) => a.player_naam)
      .sort((a, b) => a.localeCompare(b));

    const lines = [
      `🎯 Opstelling ${match.thuisteam} - ${match.uitteam}`,
      formatMatchDate(match.datum),
    ];
    if (match.locatie) lines.push(`📍 ${match.locatie}`, mapsUrl(match.locatie));
    lines.push("");
    lines.push(
      ...(spelers.length > 0 ? spelers.map((naam) => `- ${naam}`) : ["(nog niemand geselecteerd)"])
    );
    return lines.join("\n");
  }

  // Valt terug op de oude execCommand-truc met een verborgen textarea: de
  // moderne Clipboard API vereist een secure context (https) en kan op
  // sommige browsers/webviews alsnog weigeren.
  function legacyCopy(text: string) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.top = "0";
    textarea.style.left = "0";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    try {
      if (!document.execCommand("copy")) {
        throw new Error("execCommand('copy') gaf false terug");
      }
    } finally {
      document.body.removeChild(textarea);
    }
  }

  async function copyForWhatsApp() {
    const text = buildWhatsAppText();
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        legacyCopy(text);
      }
      setCopyState("copied");
    } catch {
      try {
        legacyCopy(text);
        setCopyState("copied");
      } catch {
        setCopyState("error");
      }
    } finally {
      setTimeout(() => setCopyState("idle"), 2500);
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
        {match.locatie && (
          <>
            {" · "}
            <LocatieLink locatie={match.locatie} />
          </>
        )}
      </p>

      <h2 className="mb-3 font-medium">Spelers</h2>
      <p className="mb-2 text-sm text-gray-500">
        Tik op de ster om iemand in de opstelling te zetten — ook wie "kan niet" heeft
        aangegeven, voor als er achteraf toch nog gewisseld moet worden.
      </p>
      <table className="mb-2 w-full overflow-hidden rounded-xl border border-gray-200 bg-white text-sm">
        <thead className="bg-gray-50 text-left text-gray-500">
          <tr>
            <th className="px-4 py-2 font-medium">Speler</th>
            <th className="px-4 py-2 font-medium">Status</th>
            <th className="px-4 py-2 text-center font-medium">Opstelling</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {availability.map((a) => {
            const inLineup = selected.has(a.player_id);
            return (
              <tr key={a.id}>
                <td className="px-4 py-2">{a.player_naam}</td>
                <td className="px-4 py-2">
                  <StatusBadge status={a.status} />
                </td>
                <td className="px-4 py-2 text-center">
                  <button
                    type="button"
                    onClick={() => toggle(a.player_id)}
                    aria-pressed={inLineup}
                    aria-label={
                      inLineup ? `${a.player_naam} uit opstelling halen` : `${a.player_naam} in opstelling zetten`
                    }
                    className={`text-xl leading-none ${inLineup ? "text-yellow-500" : "text-gray-300 hover:text-gray-400"}`}
                  >
                    {inLineup ? "★" : "☆"}
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="mb-6 text-sm text-gray-500">
        {beschikbaarAantal} spelers beschikbaar · {selected.size} / 4 opgesteld
      </p>

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

      <button
        onClick={copyForWhatsApp}
        className="mt-3 w-full rounded-lg border border-gray-300 py-2 font-medium text-gray-700 hover:bg-gray-50"
      >
        {copyState === "copied"
          ? "✅ Gekopieerd — plak 'm in WhatsApp"
          : copyState === "error"
            ? "⚠️ Kopiëren mislukt, probeer opnieuw"
            : "📋 Kopieer opstelling voor WhatsApp"}
      </button>

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
