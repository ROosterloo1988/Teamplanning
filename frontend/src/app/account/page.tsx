"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Nav } from "@/components/Nav";

export default function AccountPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [huidigWachtwoord, setHuidigWachtwoord] = useState("");
  const [nieuwWachtwoord, setNieuwWachtwoord] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.rol !== "CAPTAIN" && user.rol !== "BEHEER") {
      router.replace("/speler");
    }
  }, [user, loading, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setSubmitting(true);
    try {
      await api.put("/auth/me/password", {
        huidig_wachtwoord: huidigWachtwoord,
        nieuw_wachtwoord: nieuwWachtwoord,
      });
      setHuidigWachtwoord("");
      setNieuwWachtwoord("");
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
      <h1 className="mb-2 text-2xl font-bold">Mijn account</h1>
      <p className="mb-6 text-gray-500">
        Dit is het persoonlijke ontgrendelwachtwoord waarmee je als captain of beheerder inlogt,
        na het gedeelde teamwachtwoord.
      </p>

      <h2 className="mb-3 font-medium">Ontgrendelwachtwoord wijzigen</h2>
      <form onSubmit={handleSubmit} className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          type="password"
          placeholder="Huidig ontgrendelwachtwoord"
          required
          value={huidigWachtwoord}
          onChange={(e) => setHuidigWachtwoord(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />
        <input
          type="password"
          placeholder="Nieuw ontgrendelwachtwoord"
          required
          value={nieuwWachtwoord}
          onChange={(e) => setNieuwWachtwoord(e.target.value)}
          className="w-full rounded-lg border border-gray-300 px-3 py-2"
        />

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-700">✅ Wachtwoord bijgewerkt.</p>}

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
