"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { UserOut, UserRole } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

const ROL_LABELS: Record<UserRole, string> = {
  SPELER: "Speler",
  CAPTAIN: "Captain",
  BEHEER: "Beheer",
};

interface PlayerForm {
  naam: string;
  email: string;
  password: string;
  rol: UserRole;
  actief: boolean;
}

const EMPTY_FORM: PlayerForm = { naam: "", email: "", password: "", rol: "SPELER", actief: true };

export default function BeheerSpelersPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [players, setPlayers] = useState<UserOut[]>([]);
  const [form, setForm] = useState<PlayerForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editForm, setEditForm] = useState<PlayerForm>(EMPTY_FORM);
  const [editingOriginalRol, setEditingOriginalRol] = useState<UserRole>("SPELER");
  const [editError, setEditError] = useState<string | null>(null);
  const [editSubmitting, setEditSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function load() {
    const playersData = await api.get<UserOut[]>("/players/with-accounts");
    setPlayers(playersData);
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
        email: form.email.trim() || undefined,
        password: form.rol === "SPELER" ? undefined : form.password,
        rol: form.rol,
      });
      setForm(EMPTY_FORM);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(player: UserOut) {
    setEditingId(player.player_id);
    setEditingOriginalRol(player.rol);
    setEditForm({
      naam: player.naam,
      email: player.email ?? "",
      password: "",
      rol: player.rol,
      actief: player.actief,
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
      await api.put(`/players/${editingId}`, {
        naam: editForm.naam,
        email: editForm.email.trim() || null,
        rol: editForm.rol,
        actief: editForm.actief,
        password: editForm.password || undefined,
      });
      setEditingId(null);
      await load();
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setEditSubmitting(false);
    }
  }

  async function handleDelete(player: UserOut) {
    if (!window.confirm(`Weet je zeker dat je ${player.naam} wilt verwijderen? Dit kan niet ongedaan worden gemaakt.`)) {
      return;
    }
    setDeletingId(player.player_id);
    try {
      await api.delete(`/players/${player.player_id}`);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Verwijderen mislukt");
    } finally {
      setDeletingId(null);
    }
  }

  if (loading) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  const editPromotingFromSpeler = editingOriginalRol === "SPELER" && editForm.rol !== "SPELER";

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-6 text-2xl font-bold">Spelers</h1>

      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

      <ul className="mb-8 divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {players.map((p) =>
          editingId === p.player_id ? (
            <li key={p.player_id} className="px-4 py-4">
              <form onSubmit={handleEditSubmit} className="space-y-3">
                <input
                  placeholder="Naam"
                  required
                  value={editForm.naam}
                  onChange={(e) => setEditForm({ ...editForm, naam: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2"
                />
                <input
                  placeholder="E-mailadres (optioneel)"
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2"
                />
                <select
                  value={editForm.rol}
                  onChange={(e) => setEditForm({ ...editForm, rol: e.target.value as UserRole })}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2"
                >
                  <option value="SPELER">Speler</option>
                  <option value="CAPTAIN">Captain</option>
                  <option value="BEHEER">Beheer</option>
                </select>
                {editForm.rol !== "SPELER" && (
                  <input
                    placeholder={
                      editPromotingFromSpeler
                        ? "Ontgrendelwachtwoord"
                        : "Nieuw ontgrendelwachtwoord (laat leeg om ongewijzigd te laten)"
                    }
                    type="text"
                    required={editPromotingFromSpeler}
                    value={editForm.password}
                    onChange={(e) => setEditForm({ ...editForm, password: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2"
                  />
                )}
                <label className="flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    checked={editForm.actief}
                    onChange={(e) => setEditForm({ ...editForm, actief: e.target.checked })}
                    className="h-4 w-4"
                  />
                  Actief (kan inloggen en verschijnt in de naam-kiezer)
                </label>

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
            </li>
          ) : (
            <li key={p.player_id} className="flex items-center justify-between px-4 py-3 text-sm">
              <div>
                <span className={p.actief ? "" : "text-gray-400 line-through"}>{p.naam}</span>
                <span className="ml-2 text-xs text-gray-400">
                  {ROL_LABELS[p.rol]}
                  {!p.actief && " · inactief"}
                </span>
              </div>
              <div className="flex gap-3 text-xs">
                <button onClick={() => startEdit(p)} className="text-brand hover:underline">
                  Bewerken
                </button>
                <button
                  onClick={() => handleDelete(p)}
                  disabled={deletingId === p.player_id}
                  className="text-red-600 hover:underline disabled:opacity-50"
                >
                  {deletingId === p.player_id ? "Bezig..." : "Verwijderen"}
                </button>
              </div>
            </li>
          )
        )}
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
          placeholder="E-mailadres (optioneel)"
          type="email"
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
            🎯 Speler logt in door zijn naam te kiezen op het inlogscherm — geen wachtwoord nodig.
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
