"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { MatchOut, MatchReminderOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { formatMatchDate } from "@/components/StatusBadge";

export default function CaptainMatchesPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [matches, setMatches] = useState<MatchOut[]>([]);
  const [reminders, setReminders] = useState<MatchReminderOut[]>([]);
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
    Promise.all([
      api.get<MatchOut[]>("/matches?upcoming_only=true"),
      api.get<MatchReminderOut[]>("/matches/reminders"),
    ])
      .then(([matchesData, remindersData]) => {
        setMatches(matchesData);
        setReminders(remindersData);
      })
      .finally(() => setFetching(false));
  }, [user, loading, router]);

  if (loading || fetching) {
    return <div className="py-10 text-center text-gray-400">Laden...</div>;
  }

  return (
    <div>
      <Nav />
      <h1 className="mb-4 text-2xl font-bold">Aankomende wedstrijden</h1>

      {reminders.length > 0 && (
        <div className="mb-6 space-y-2">
          {reminders.map((r) => (
            <Link
              key={r.match.id}
              href={`/captain/${r.match.id}`}
              className="block rounded-lg bg-amber-50 p-3 text-sm text-amber-800 hover:bg-amber-100"
            >
              ⚠️ Voor <span className="font-medium capitalize">{formatMatchDate(r.match.datum)}</span> hebben{" "}
              {r.missing} van de {r.total} spelers nog niet gereageerd.
            </Link>
          ))}
        </div>
      )}

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
