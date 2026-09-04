"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace("/login");
    } else if (user.rol === "BEHEER") {
      router.replace("/beheer");
    } else if (user.rol === "CAPTAIN") {
      router.replace("/captain");
    } else {
      router.replace("/speler");
    }
  }, [user, loading, router]);

  return (
    <div className="flex min-h-[50vh] items-center justify-center text-gray-400">
      🎯 Laden...
    </div>
  );
}
