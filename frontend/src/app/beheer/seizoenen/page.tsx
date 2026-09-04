"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { SeasonOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerSeizoenenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [form, setForm] = useState({ naam: "", startjaar: "" });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [activating, setActivating] = useState<number | null>(null);

  async function load() {
    const data = await api.get<SeasonOut[]>("/seasons");
    setSeasons(data);
  }

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
    load();
  }, [user, loading, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/seasons", {
        naam: form.naam,
        startjaar: Number(form.startjaar),
      });
      setForm({ naam: "", startjaar: "" });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setSubmitting(false);
    }
  }

  async function activate(id: number) {
    setActivating(id);
    try {
      await api.post(`/seasons/${id}/activate`);
      await load();
    } finally {
      setActivating(null);
    }
  }

  if (loading) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-2 text-2xl font-bold">Seizoenen</h1>
      <p className="mb-6 text-gray-500">
        Het actieve seizoen wordt automatisch gekoppeld aan nieuwe wedstrijden.
      </p>

      <ul className="mb-8 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {seasons.map((s) => (
          <li key={s.id} className="flex items-center justify-between px-4 py-3 text-sm">
            <span>
              {s.naam}
              <span className="ml-2 text-gray-400">
                ({s.startjaar}–{s.eindjaar})
              </span>
              {s.actief && (
                <span className="ml-2 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                  Actief
                </span>
              )}
            </span>
            {!s.actief && (
              <button
                onClick={() => activate(s.id)}
                disabled={activating === s.id}
                className="rounded-lg border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
              >
                {activating === s.id ? "Bezig..." : "Activeren"}
              </button>
            )}
          </li>
        ))}
        {seasons.length === 0 && (
          <li className="px-4 py-6 text-center text-gray-400">Geen seizoenen</li>
        )}
      </ul>

      <h2 className="mb-3 font-medium">Seizoen toevoegen</h2>
      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          placeholder="Naam (bv. 2026-2027)"
          required
          value={form.naam}
          onChange={(e) => setForm({ ...form, naam: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          type="number"
          placeholder="Startjaar (bv. 2026 voor seizoen 2026-2027)"
          required
          value={form.startjaar}
          onChange={(e) => setForm({ ...form, startjaar: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <p className="text-sm text-gray-500">Eindjaar wordt automatisch startjaar + 1.</p>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {submitting ? "Bezig..." : "Seizoen toevoegen"}
        </button>
      </form>
    </div>
  );
}
