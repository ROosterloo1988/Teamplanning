"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { PlayerOut, TeamOut, UserRole } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerSpelersPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [players, setPlayers] = useState<PlayerOut[]>([]);
  const [teams, setTeams] = useState<TeamOut[]>([]);
  const [form, setForm] = useState({
    naam: "",
    email: "",
    password: "",
    rol: "SPELER" as UserRole,
    team_id: "" as string,
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const [playersData, teamsData] = await Promise.all([
      api.get<PlayerOut[]>("/players"),
      api.get<TeamOut[]>("/teams"),
    ]);
    setPlayers(playersData);
    setTeams(teamsData);
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
      await api.post("/players/with-account", {
        naam: form.naam,
        email: form.email,
        password: form.rol === "SPELER" ? undefined : form.password,
        rol: form.rol,
        team_id: form.team_id ? Number(form.team_id) : null,
      });
      setForm({ naam: "", email: "", password: "", rol: "SPELER", team_id: "" });
      await load();
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
      <h1 className="mb-6 text-2xl font-bold">Spelers</h1>

      <ul className="mb-8 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {players.map((p) => (
          <li key={p.id} className="px-4 py-3 text-sm">
            {p.naam}
          </li>
        ))}
        {players.length === 0 && <li className="px-4 py-6 text-center text-gray-400">Geen spelers</li>}
      </ul>

      <h2 className="mb-3 font-medium">Nieuwe speler toevoegen</h2>
      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          placeholder="Naam"
          required
          value={form.naam}
          onChange={(e) => setForm({ ...form, naam: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          placeholder="E-mailadres"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <select
          value={form.rol}
          onChange={(e) => setForm({ ...form, rol: e.target.value as UserRole })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        >
          <option value="SPELER">Speler</option>
          <option value="CAPTAIN">Captain</option>
          <option value="BEHEER">Beheer</option>
        </select>
        {form.rol === "SPELER" ? (
          <p className="text-sm text-gray-500">
            🏓 Speler logt in door zijn naam te kiezen op het inlogscherm — geen wachtwoord nodig.
          </p>
        ) : (
          <input
            placeholder="Ontgrendelwachtwoord"
            type="text"
            required
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        )}
        <select
          value={form.team_id}
          onChange={(e) => setForm({ ...form, team_id: e.target.value })}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        >
          <option value="">Geen team</option>
          {teams.map((t) => (
            <option key={t.id} value={t.id}>
              {t.naam}
            </option>
          ))}
        </select>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {submitting ? "Bezig..." : "Speler toevoegen"}
        </button>
      </form>
    </div>
  );
}
