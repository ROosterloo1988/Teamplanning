"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { NotificationBell } from "@/components/NotificationBell";

export function Nav() {
  const { user, logout } = useAuth();
  if (!user) return null;

  return (
    <nav className="mb-6 flex flex-wrap items-center justify-between gap-x-2 gap-y-2 border-b border-gray-200 pb-3">
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-sm font-medium">
        <Link href="/speler" className="whitespace-nowrap hover:text-brand">
          Speler
        </Link>
        {(user.rol === "CAPTAIN" || user.rol === "BEHEER") && (
          <Link href="/captain" className="whitespace-nowrap hover:text-brand">
            Captain
          </Link>
        )}
        {user.rol === "BEHEER" && (
          <Link href="/beheer" className="whitespace-nowrap hover:text-brand">
            Beheer
          </Link>
        )}
        <Link href="/geschiedenis" className="whitespace-nowrap hover:text-brand">
          Historie
        </Link>
        <Link href="/overzicht" className="whitespace-nowrap hover:text-brand">
          Overzicht
        </Link>
      </div>
      <div className="flex items-center gap-3">
        {(user.rol === "CAPTAIN" || user.rol === "BEHEER") && (
          <Link href="/account" className="text-sm text-gray-500 hover:text-gray-800" title="Mijn account">
            ⚙️
          </Link>
        )}
        <NotificationBell />
        <button onClick={logout} className="whitespace-nowrap text-sm text-gray-500 hover:text-gray-800">
          Uitloggen
        </button>
      </div>
    </nav>
  );
}
