"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerInstellingenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.rol !== "BEHEER") {
      router.replace("/speler");
    }
  }, [user, loading, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setSubmitting(true);
    try {
      await api.put("/auth/team-password", { password });
      setPassword("");
      setSuccess(true);
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
      <h1 className="mb-2 text-2xl font-bold">Instellingen</h1>
      <p className="mb-6 text-gray-500">
        Het teamwachtwoord beschermt het inlogscherm voordat de naam-kiezer verschijnt. Iedereen
        met dit wachtwoord kan iedere speler zien en als hen inloggen — captain- en
        beheerfuncties blijven daarna nog apart vergrendeld met een persoonlijk
        ontgrendelwachtwoord.
      </p>

      <h2 className="mb-3 font-medium">Teamwachtwoord wijzigen</h2>
      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          type="text"
          placeholder="Nieuw teamwachtwoord"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-700">✅ Teamwachtwoord bijgewerkt.</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {submitting ? "Bezig..." : "Wachtwoord opslaan"}
        </button>
      </form>
    </div>
  );
}
