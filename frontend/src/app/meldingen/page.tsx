"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { NotificationOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { PushToggle } from "@/components/PushToggle";

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("nl-NL", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function MeldingenPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationOut[]>([]);
  const [fetching, setFetching] = useState(true);

  async function load() {
    const data = await api.get<NotificationOut[]>("/notifications/me");
    setNotifications(data);
  }

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
      return;
    }
    load().finally(() => setFetching(false));
  }, [user, loading, router]);

  async function handleClick(n: NotificationOut) {
    if (!n.read_at) {
      const updated = await api.post<NotificationOut>(`/notifications/${n.id}/read`);
      setNotifications((prev) => prev.map((x) => (x.id === n.id ? updated : x)));
    }
    if (n.match_id && (user?.rol === "CAPTAIN" || user?.rol === "BEHEER")) {
      router.push(`/captain/${n.match_id}`);
    }
  }

  async function markAllRead() {
    await api.post("/notifications/read-all");
    await load();
  }

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  const hasUnread = notifications.some((n) => !n.read_at);

  return (
    <div>
      <Nav />
      <PushToggle />
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Meldingen</h1>
        {hasUnread && (
          <button onClick={markAllRead} className="text-sm text-brand hover:underline">
            Alles gelezen
          </button>
        )}
      </div>

      <ul className="divide-y divide-gray-200 rounded-xl border border-gray-200 bg-white">
        {notifications.map((n) => (
          <li key={n.id}>
            <button
              onClick={() => handleClick(n)}
              className={`flex w-full flex-col gap-1 px-4 py-3 text-left hover:bg-gray-50 ${
                !n.read_at ? "bg-blue-50/50" : ""
              }`}
            >
              <div className="flex items-center gap-2">
                {!n.read_at && <span className="h-2 w-2 rounded-full bg-brand" />}
                <span className="font-medium">{n.title}</span>
              </div>
              {n.body && <span className="text-sm text-gray-600">{n.body}</span>}
              <span className="text-xs text-gray-400">{formatTimestamp(n.created_at)}</span>
            </button>
          </li>
        ))}
        {notifications.length === 0 && (
          <li className="px-4 py-6 text-center text-gray-400">Geen meldingen</li>
        )}
      </ul>
    </div>
  );
}
