"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { AuditLogOut } from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";
import { AuditLogList } from "@/components/AuditLogList";

const PAGE_SIZE = 50;

export default function BeheerLogboekPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [entries, setEntries] = useState<AuditLogOut[]>([]);
  const [fetching, setFetching] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);

  const loadPage = useCallback(async (offset: number) => {
    const page = await api.get<AuditLogOut[]>(`/audit-log?limit=${PAGE_SIZE}&offset=${offset}`);
    setHasMore(page.length === PAGE_SIZE);
    return page;
  }, []);

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
    loadPage(0)
      .then(setEntries)
      .finally(() => setFetching(false));
  }, [user, loading, router, loadPage]);

  async function loadMore() {
    setLoadingMore(true);
    try {
      const page = await loadPage(entries.length);
      setEntries((prev) => [...prev, ...page]);
    } finally {
      setLoadingMore(false);
    }
  }

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <h1 className="mb-2 text-2xl font-bold">Logboek</h1>
      <p className="mb-6 text-gray-500">Wie heeft wat gewijzigd, zie ontwerp sectie 10.</p>

      <AuditLogList entries={entries} />

      {hasMore && (
        <button
          onClick={loadMore}
          disabled={loadingMore}
          className="mt-4 w-full rounded-lg border border-gray-300 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
        >
          {loadingMore ? "Bezig..." : "Meer laden"}
        </button>
      )}
    </div>
  );
}
