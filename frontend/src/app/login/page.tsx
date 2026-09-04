"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { ApiError, api, getTeamToken, setTeamToken, teamApi } from "@/lib/api";
import { AccountOption } from "@/lib/types";

export default function LoginPage() {
  const { enter } = useAuth();
  const router = useRouter();

  // Stap 1: gedeeld teamwachtwoord (alleen nodig als dit toestel het nog
  // niet eerder heeft ingevoerd).
  const [checkingTeamToken, setCheckingTeamToken] = useState(true);
  const [hasTeamAccess, setHasTeamAccess] = useState(false);
  const [teamPassword, setTeamPassword] = useState("");
  const [teamError, setTeamError] = useState<string | null>(null);
  const [teamSubmitting, setTeamSubmitting] = useState(false);

  // Stap 2: naam-kiezer.
  const [accounts, setAccounts] = useState<AccountOption[] | null>(null);
  const [selected, setSelected] = useState<AccountOption | null>(null);
  const [unlockPassword, setUnlockPassword] = useState("");
  const [enterError, setEnterError] = useState<string | null>(null);
  const [entering, setEntering] = useState(false);

  const loadAccounts = useCallback(async () => {
    try {
      const data = await teamApi.get<AccountOption[]>("/auth/accounts");
      setAccounts(data);
      setHasTeamAccess(true);
    } catch {
      // Teamtoken ontbreekt, is verlopen, of ongeldig: terug naar stap 1.
      setHasTeamAccess(false);
    } finally {
      setCheckingTeamToken(false);
    }
  }, []);

  useEffect(() => {
    if (getTeamToken()) {
      loadAccounts();
    } else {
      setCheckingTeamToken(false);
    }
  }, [loadAccounts]);

  async function handleTeamSubmit(e: React.FormEvent) {
    e.preventDefault();
    setTeamError(null);
    setTeamSubmitting(true);
    try {
      const token = await api.post<{ access_token: string }>("/auth/team-access", {
        password: teamPassword,
      });
      setTeamToken(token.access_token);
      setTeamPassword("");
      await loadAccounts();
    } catch (err) {
      setTeamError(err instanceof ApiError ? err.message : "Inloggen mislukt");
    } finally {
      setTeamSubmitting(false);
    }
  }

  function pickAccount(account: AccountOption) {
    setEnterError(null);
    setUnlockPassword("");
    if (account.rol === "SPELER") {
      void doEnter(account.id, account.rol);
    } else {
      setSelected(account);
    }
  }

  async function doEnter(userId: number, rol: AccountOption["rol"], password?: string) {
    setEnterError(null);
    setEntering(true);
    try {
      await enter(userId, password);
      // Landingspagina per rol: een beheer- of captain-account hoeft geen
      // gekoppeld spelerprofiel te hebben (bv. het initiele bootstrap-account),
      // dus die sturen we niet standaard naar /speler.
      const destination = rol === "BEHEER" ? "/beheer" : rol === "CAPTAIN" ? "/captain" : "/speler";
      router.push(destination);
    } catch (err) {
      setEnterError(err instanceof ApiError ? err.message : "Inloggen mislukt");
    } finally {
      setEntering(false);
    }
  }

  async function handleUnlockSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selected) return;
    await doEnter(selected.id, selected.rol, unlockPassword);
  }

  // Spelers (inclusief captains, want die zijn ook gewoon speler) zijn de
  // grote, prominente knoppen; alleen de beheerder staat als kleinere sectie
  // onderaan, zodat die niet meer even groot tussen de spelers staat.
  const spelers = (accounts ?? []).filter((a) => a.rol !== "BEHEER");
  const overigen = (accounts ?? []).filter((a) => a.rol === "BEHEER");

  if (checkingTeamToken) {
    return <div className="py-10 text-center text-gray-400">🎯 Laden...</div>;
  }

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center">
      <h1 className="mb-1 text-2xl font-bold">🎯 De Gouv</h1>

      {!hasTeamAccess && (
        <>
          <p className="mb-6 text-gray-500">Voer het teamwachtwoord in</p>
          <form onSubmit={handleTeamSubmit} className="w-full max-w-xs space-y-4">
            <input
              type="password"
              placeholder="Teamwachtwoord"
              required
              autoFocus
              value={teamPassword}
              onChange={(e) => setTeamPassword(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-brand focus:outline-none"
            />
            {teamError && <p className="text-sm text-red-600">{teamError}</p>}
            <button
              type="submit"
              disabled={teamSubmitting}
              className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
            >
              {teamSubmitting ? "Bezig..." : "Verder"}
            </button>
          </form>
        </>
      )}

      {hasTeamAccess && !accounts && (
        <p className="text-gray-400">Laden...</p>
      )}

      {hasTeamAccess && accounts && (
        <div className="w-full max-w-xs">
          <p className="mb-4 text-center text-gray-500">Ik ben:</p>
          <ul className="space-y-2">
            {spelers.map((account) => (
              <AccountRow
                key={account.id}
                account={account}
                selected={selected}
                entering={entering}
                unlockPassword={unlockPassword}
                setUnlockPassword={setUnlockPassword}
                onPick={pickAccount}
                onUnlockSubmit={handleUnlockSubmit}
              />
            ))}
          </ul>

          {overigen.length > 0 && (
            <>
              <p className="mb-2 mt-6 text-center text-xs text-gray-400">Beheerder</p>
              <ul className="space-y-1.5">
                {overigen.map((account) => (
                  <AccountRow
                    key={account.id}
                    account={account}
                    selected={selected}
                    entering={entering}
                    unlockPassword={unlockPassword}
                    setUnlockPassword={setUnlockPassword}
                    onPick={pickAccount}
                    onUnlockSubmit={handleUnlockSubmit}
                    compact
                  />
                ))}
              </ul>
            </>
          )}

          {enterError && <p className="mt-3 text-center text-sm text-red-600">{enterError}</p>}
        </div>
      )}
    </div>
  );
}

function AccountRow({
  account,
  selected,
  entering,
  unlockPassword,
  setUnlockPassword,
  onPick,
  onUnlockSubmit,
  compact = false,
}: {
  account: AccountOption;
  selected: AccountOption | null;
  entering: boolean;
  unlockPassword: string;
  setUnlockPassword: (value: string) => void;
  onPick: (account: AccountOption) => void;
  onUnlockSubmit: (e: React.FormEvent) => void;
  compact?: boolean;
}) {
  return (
    <li>
      <button
        onClick={() => onPick(account)}
        disabled={entering}
        className={
          compact
            ? "flex w-full items-center justify-between rounded-lg border border-gray-200 px-3 py-1.5 text-left text-sm text-gray-500 hover:bg-gray-50 disabled:opacity-50"
            : "flex w-full items-center justify-between rounded-lg border border-gray-300 px-4 py-3 text-left font-medium hover:bg-gray-50 disabled:opacity-50"
        }
      >
        {account.naam}
        {account.rol !== "SPELER" && <span aria-label="ontgrendelwachtwoord nodig">🔒</span>}
      </button>

      {selected?.id === account.id && (
        <form onSubmit={onUnlockSubmit} className="mt-2 space-y-2 pl-1">
          <input
            type="password"
            placeholder="Ontgrendelwachtwoord"
            required
            autoFocus
            value={unlockPassword}
            onChange={(e) => setUnlockPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand focus:outline-none"
          />
          <button
            type="submit"
            disabled={entering}
            className="w-full rounded-lg bg-brand py-1.5 text-sm font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {entering ? "Bezig..." : "Ontgrendelen"}
          </button>
        </form>
      )}
    </li>
  );
}
