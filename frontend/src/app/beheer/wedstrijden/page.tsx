"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { MatchOut, MatchType, SeasonOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";
import { formatMatchDate } from "@/components/StatusBadge";

const TYPE_LABELS: Record<MatchType, string> = {
  COMPETITIE: "Competitie",
  BEKER: "Beker",
  INHAAL: "Inhaal",
  OVERIG: "Overig",
};

export default function BeheerWedstrijdenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [seasonFilter, setSeasonFilter] = useState<string>("");
  const [form, setForm] = useState({
    datum: "",
    thuisteam: "",
    uitteam: "",
    locatie: "",
    type: "COMPETITIE" as MatchType,
    nummer: "",
    season_id: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const loadMatches = useCallback(async (seasonId: string) => {
    const query = seasonId ? `?season_id=${seasonId}` : "";
    const data = await api.get<MatchOut[]>(`/matches${query}`);
    setMatches(data.sort((a, b) => b.datum.localeCompare(a.datum)));
  }, []);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.rol !== "BEHEER") {
      router.replace("/speler");
      return;
    }
    Promise.all([loadMatches(""), api.get<SeasonOut[]>("/seasons")]).then(([, seasonsData]) => {
      setSeasons(seasonsData);
      const active = seasonsData.find((s) => s.actief);
      if (active) setForm((f) => ({ ...f, season_id: String(active.id) }));
    });
  }, [user, loading, router, loadMatches]);

  function seasonNaam(seasonId: number | null): string {
    if (!seasonId) return "—";
    return seasons.find((s) => s.id === seasonId)?.naam ?? "—";
  }

  async function handleFilterChange(value: string) {
    setSeasonFilter(value);
    await loadMatches(value);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/matches", {
        ...form,
        nummer: form.nummer || null,
        locatie: form.locatie || null,
        season_id: form.season_id ? Number(form.season_id) : null,
      });
      setForm((f) => ({ ...f, datum: "", thuisteam: "", uitteam: "", locatie: "", nummer: "" }));
      await loadMatches(seasonFilter);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Wedstrijden</h1>
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

      <table className="mb-8 w-full overflow-hidden rounded-xl border border-gray-200 bg-white text-sm">
        <thead className="bg-gray-50 text-left text-gray-500">
          <tr>
            <th className="px-3 py-2 font-medium">Datum</th>
            <th className="px-3 py-2 font-medium">Thuis</th>
            <th className="px-3 py-2 font-medium">Uit</th>
            <th className="px-3 py-2 font-medium">Locatie</th>
            <th className="px-3 py-2 font-medium">Type</th>
            <th className="px-3 py-2 font-medium">Seizoen</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {matches.map((m) => (
            <tr key={m.id}>
              <td className="px-3 py-2 capitalize">{formatMatchDate(m.datum)}</td>
              <td className="px-3 py-2">{m.thuisteam}</td>
              <td className="px-3 py-2">{m.uitteam}</td>
              <td className="px-3 py-2">{m.locatie ?? "—"}</td>
              <td className="px-3 py-2">{TYPE_LABELS[m.type]}</td>
              <td className="px-3 py-2">{seasonNaam(m.season_id)}</td>
            </tr>
          ))}
          {matches.length === 0 && (
            <tr>
              <td colSpan={6} className="px-3 py-6 text-center text-gray-400">
                Geen wedstrijden
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <h2 className="mb-3 font-medium">Wedstrijd toevoegen</h2>
      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          type="date"
          required
          value={form.datum}
          onChange={(e) => setForm({ ...form, datum: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          placeholder="Thuisteam"
          required
          value={form.thuisteam}
          onChange={(e) => setForm({ ...form, thuisteam: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          placeholder="Uitteam"
          required
          value={form.uitteam}
          onChange={(e) => setForm({ ...form, uitteam: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          placeholder="Locatie"
          value={form.locatie}
          onChange={(e) => setForm({ ...form, locatie: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <select
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value as MatchType })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        >
          {Object.entries(TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select
          value={form.season_id}
          onChange={(e) => setForm({ ...form, season_id: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        >
          <option value="">Geen seizoen</option>
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.naam}
              {s.actief ? " (actief)" : ""}
            </option>
          ))}
        </select>
        <input
          placeholder="Wedstrijdnummer (optioneel)"
          value={form.nummer}
          onChange={(e) => setForm({ ...form, nummer: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {submitting ? "Bezig..." : "Wedstrijd toevoegen"}
        </button>
      </form>
    </div>
  );
}
