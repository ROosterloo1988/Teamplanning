"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { MatchOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDate } from "@/components/StatusBadge";

export default function CaptainMatchesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [fetching, setFetching] = useState(true);

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.rol !== "CAPTAIN" && user.rol !== "BEHEER") {
      router.replace("/speler");
      return;
    }
    api
      .get<MatchOut[]>("/matches?upcoming_only=true")
      .then(setMatches)
      .finally(() => setFetching(false));
  }, [user, loading, router]);

  if (loading || fetching) {
    return <div className="py-10 text-center text-gray-400">Laden...</div>;
  }

  return (
    <div>
      <Nav />
      <h1 className="mb-6 text-2xl font-bold">Aankomende wedstrijden</h1>
      <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {matches.map((match) => (
          <li key={match.id}>
            <Link
              href={`/captain/${match.id}`}
              className="flex flex-col gap-1 px-4 py-3 hover:bg-gray-50"
            >
              <span className="text-sm text-gray-500 capitalize">{formatMatchDate(match.datum)}</span>
              <span className="font-medium">
                {match.thuisteam} - {match.uitteam}
              </span>
            </Link>
          </li>
        ))}
        {matches.length === 0 && <li className="px-4 py-6 text-center text-gray-400">Geen wedstrijden</li>}
      </ul>
    </div>
  );
}
