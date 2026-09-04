"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerDashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [fetching, setFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
    api
      .get<DashboardStats>("/admin/dashboard")
      .then(setStats)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Laden mislukt"))
      .finally(() => setFetching(false));
  }, [user, loading, router]);

  if (loading || fetching) {
    return <div className="py-10 text-center text-gray-400">Laden...</div>;
  }

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-6 text-2xl font-bold">Dashboard</h1>
      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}
      {stats && (
        <div className="grid grid-cols-2 gap-4">
          <StatCard label="👥 Spelers" value={stats.spelers} />
          <StatCard label="🎯 Wedstrijden" value={stats.wedstrijden} />
          <StatCard label="🟢 Compleet ingevuld" value={stats.wedstrijden_compleet} />
          <StatCard label="⚠️ Missen antwoorden" value={stats.wedstrijden_missen_antwoorden} />
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
    </div>
  );
}
