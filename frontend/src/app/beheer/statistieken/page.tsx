"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { PlayerStatsOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";

export default function BeheerStatistiekenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<PlayerStatsOut[]>([]);
  const [fetching, setFetching] = useState(true);

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
      .get<PlayerStatsOut[]>("/stats/players")
      .then(setStats)
      .finally(() => setFetching(false));
  }, [user, loading, router]);

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-2 text-2xl font-bold">Statistieken</h1>
      <p className="mb-6 text-gray-500">Reactiepercentage en beschikbaarheid per speler.</p>

      <div className="space-y-3">
        {stats.map((s) => (
          <div key={s.player_id} className="rounded-xl border border-gray-200 bg-white p-4">
            <div className="mb-2 flex items-baseline justify-between">
              <span className="font-medium">{s.player_naam}</span>
              <span className="text-sm text-gray-500">{s.response_rate}% gereageerd</span>
            </div>
            <div className="mb-3 h-2 w-full overflow-hidden rounded-full bg-gray-100">
              <div
                className="h-full rounded-full bg-brand"
                style={{ width: `${s.response_rate}%` }}
              />
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-gray-600 sm:grid-cols-5">
              <span>🟢 Kan: {s.beschikbaar}</span>
              <span>🔴 Kan niet: {s.niet_beschikbaar}</span>
              <span>🟡 Indien nodig: {s.indien_nodig}</span>
              <span>⚪ Geen antwoord: {s.geen_antwoord}</span>
              <span>🏓 Opgesteld: {s.keer_opgesteld}×</span>
            </div>
          </div>
        ))}
        {stats.length === 0 && <p className="text-center text-gray-400">Geen spelers gevonden</p>}
      </div>
    </div>
  );
}
