"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { api, clearToken, setToken as storeToken, teamApi } from "./api";
import { UserOut } from "./types";

interface AuthContextValue {
  user: UserOut | null;
  loading: boolean;
  enter: (userId: number, unlockPassword?: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  async function refresh() {
    try {
      const me = await api.get<UserOut>("/auth/me");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function enter(userId: number, unlockPassword?: string) {
    const token = await teamApi.post<{ access_token: string }>("/auth/enter", {
      user_id: userId,
      unlock_password: unlockPassword,
    });
    storeToken(token.access_token);
    await refresh();
  }

  function logout() {
    // Alleen het persoonlijke token wissen: het teamtoken (voorbij de
    // gedeelde teamwachtwoord-poort) blijft geldig op dit toestel, zodat je
    // direct terugkomt bij de naam-kiezer in plaats van opnieuw het
    // teamwachtwoord te moeten intypen.
    clearToken();
    setUser(null);
    router.push("/login");
  }

  return (
    <AuthContext.Provider value={{ user, loading, enter, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth moet binnen AuthProvider gebruikt worden");
  return ctx;
}
