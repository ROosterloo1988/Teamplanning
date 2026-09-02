"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

interface ImportResult {
  matches_created: number;
  matches_updated: number;
  players_created: number;
  availability_upserted: number;
}

export default function BeheerImportPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
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
    if (!file) return;
    setError(null);
    setResult(null);
    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await api.post<ImportResult>("/admin/import/excel", formData);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Importeren mislukt");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-2 text-2xl font-bold">Excel importeren</h1>
      <p className="mb-6 text-gray-500">
        Upload het bestaande planningsbestand (bijv. &quot;Schema seizoen 26-27-3.xlsx&quot;). Wedstrijden,
        spelers en beschikbaarheden worden automatisch ingelezen en geconverteerd (v/x/?/1 → status).
      </p>

      <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-gray-200 bg-white p-4">
        <input
          type="file"
          accept=".xlsx"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="w-full text-sm"
        />
        <button
          type="submit"
          disabled={!file || submitting}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {submitting ? "Bezig met importeren..." : "Importeren"}
        </button>
      </form>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="mt-6 rounded-xl border border-green-200 bg-green-50 p-4 text-sm text-green-800">
          <p className="mb-2 font-medium">✅ Import voltooid</p>
          <ul className="space-y-1">
            <li>{result.matches_created} nieuwe wedstrijden</li>
            <li>{result.matches_updated} bestaande wedstrijden bijgewerkt</li>
            <li>{result.players_created} nieuwe spelers</li>
            <li>{result.availability_upserted} beschikbaarheden verwerkt</li>
          </ul>
        </div>
      )}
    </div>
  );
}
