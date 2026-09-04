"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { MatchOut, MatchType, SeasonOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";
import { formatMatchDate, LocatieLink } from "@/components/StatusBadge";

const TYPE_LABELS: Record<MatchType, string> = {
  COMPETITIE: "Competitie",
  BEKER: "Beker",
  INHAAL: "Inhaal",
  OVERIG: "Overig",
};

interface MatchForm {
  datum: string;
  thuisteam: string;
  uitteam: string;
  locatie: string;
  type: MatchType;
  nummer: string;
  season_id: string;
}

const EMPTY_FORM: MatchForm = {
  datum: "",
  thuisteam: "",
  uitteam: "",
  locatie: "",
  type: "COMPETITIE",
  nummer: "",
  season_id: "",
};

export default function BeheerWedstrijdenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [seasonFilter, setSeasonFilter] = useState<string>("");
  const [form, setForm] = useState<MatchForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<MatchForm>(EMPTY_FORM);
  const [editError, setEditError] = useState<string | null>(null);
  const [editSubmitting, setEditSubmitting] = useState(false);

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

  function startEdit(match: MatchOut) {
    setEditingId(match.id);
    setEditForm({
      datum: match.datum,
      thuisteam: match.thuisteam,
      uitteam: match.uitteam,
      locatie: match.locatie ?? "",
      type: match.type,
      nummer: match.nummer ?? "",
      season_id: match.season_id ? String(match.season_id) : "",
    });
    setEditError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditError(null);
  }

  async function handleEditSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (editingId === null) return;
    setEditError(null);
    setEditSubmitting(true);
    try {
      await api.put(`/matches/${editingId}`, {
        datum: editForm.datum,
        thuisteam: editForm.thuisteam,
        uitteam: editForm.uitteam,
        locatie: editForm.locatie || null,
        type: editForm.type,
        nummer: editForm.nummer || null,
        season_id: editForm.season_id ? Number(editForm.season_id) : null,
      });
      setEditingId(null);
      await loadMatches(seasonFilter);
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setEditSubmitting(false);
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

      <div className="mb-8 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white text-sm">
        {matches.length === 0 && <p className="px-3 py-6 text-center text-gray-400">Geen wedstrijden</p>}
        {matches.map((m) =>
          editingId === m.id ? (
            <form
              key={m.id}
              onSubmit={handleEditSubmit}
              className="space-y-3 px-4 py-4"
            >
              <input
                type="date"
                required
                value={editForm.datum}
                onChange={(e) => setEditForm({ ...editForm, datum: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
              <input
                placeholder="Thuisteam"
                required
                value={editForm.thuisteam}
                onChange={(e) => setEditForm({ ...editForm, thuisteam: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
              <input
                placeholder="Uitteam"
                required
                value={editForm.uitteam}
                onChange={(e) => setEditForm({ ...editForm, uitteam: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
              <input
                placeholder="Locatie (adres, zodat Google Maps ermee kan navigeren)"
                value={editForm.locatie}
                onChange={(e) => setEditForm({ ...editForm, locatie: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />
              <select
                value={editForm.type}
                onChange={(e) => setEditForm({ ...editForm, type: e.target.value as MatchType })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              >
                {Object.entries(TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
              <select
                value={editForm.season_id}
                onChange={(e) => setEditForm({ ...editForm, season_id: e.target.value })}
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
                value={editForm.nummer}
                onChange={(e) => setEditForm({ ...editForm, nummer: e.target.value })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2"
              />

              {editError && <p className="text-sm text-red-600">{editError}</p>}

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="flex-1 rounded-lg border border-gray-300 py-2 font-medium text-gray-700 hover:bg-gray-50"
                >
                  Annuleren
                </button>
                <button
                  type="submit"
                  disabled={editSubmitting}
                  className="flex-1 rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
                >
                  {editSubmitting ? "Bezig..." : "Opslaan"}
                </button>
              </div>
            </form>
          ) : (
            <div key={m.id} className="flex items-center justify-between gap-3 px-3 py-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-x-2 text-gray-500">
                  <span className="capitalize">{formatMatchDate(m.datum)}</span>
                  <span>·</span>
                  <span>{TYPE_LABELS[m.type]}</span>
                  <span>·</span>
                  <span>{seasonNaam(m.season_id)}</span>
                </div>
                <div className="font-medium">
                  {m.thuisteam} - {m.uitteam}
                </div>
                {m.locatie && (
                  <div className="mt-0.5">
                    <LocatieLink locatie={m.locatie} />
                  </div>
                )}
              </div>
              <button
                onClick={() => startEdit(m)}
                className="shrink-0 text-xs font-medium text-brand hover:underline"
              >
                Bewerken
              </button>
            </div>
          )
        )}
      </div>

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
          placeholder="Locatie (adres, zodat Google Maps ermee kan navigeren)"
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
