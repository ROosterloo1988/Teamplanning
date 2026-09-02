"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { DashboardStats } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerDashboardPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);

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
    api.get<DashboardStats>("/admin/dashboard").then(setStats);
  }, [user, loading, router]);

  if (loading || !stats) {
    return <div className="py-10 text-center text-gray-400">Laden...</div>;
  }

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-6 text-2xl font-bold">Dashboard</h1>
      <div className="grid grid-cols-2 gap-4">
        <StatCard label="👥 Spelers" value={stats.spelers} />
        <StatCard label="🏓 Wedstrijden" value={stats.wedstrijden} />
        <StatCard label="🟢 Compleet ingevuld" value={stats.wedstrijden_compleet} />
        <StatCard label="⚠️ Missen antwoorden" value={stats.wedstrijden_missen_antwoorden} />
      </div>
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
