"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { NotificationBell } from "@/components/NotificationBell";

export function Nav() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <nav className="mb-6 flex items-center justify-between border-b border-gray-200 pb-3">
      <div className="flex gap-4 text-sm font-medium">
        <Link href="/speler" className="hover:text-brand">
          🎯 Speler
        </Link>
        {(user.rol === "CAPTAIN" || user.rol === "BEHEER") && (
          <Link href="/captain" className="hover:text-brand">
            Captain
          </Link>
        )}
        {user.rol === "BEHEER" && (
          <Link href="/beheer" className="hover:text-brand">
            Beheer
          </Link>
        )}
        <Link href="/geschiedenis" className="hover:text-brand">
          Geschiedenis
        </Link>
      </div>
      <div className="flex items-center gap-3">
        {(user.rol === "CAPTAIN" || user.rol === "BEHEER") && (
          <Link href="/account" className="text-sm text-gray-500 hover:text-gray-800" title="Mijn account">
            ⚙️
          </Link>
        )}
        <NotificationBell />
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-800">
          Uitloggen
        </button>
      </div>
    </nav>
  );
}
