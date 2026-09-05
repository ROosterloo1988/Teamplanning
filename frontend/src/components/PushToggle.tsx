"use client";

import { useEffect, useState } from "react";
import {
  getCurrentSubscription,
  isPushSupported,
  registerServiceWorker,
  subscribeToPush,
  unsubscribeFromPush,
} from "@/lib/push";

export function PushToggle() {
  const [supported, setSupported] = useState(true);
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    if (!isPushSupported()) {
      setSupported(false);
      setChecking(false);
      return;
    }
    registerServiceWorker()
      .then(() => getCurrentSubscription())
      .then((sub) => setSubscribed(!!sub))
      .finally(() => setChecking(false));
  }, []);

  async function handleToggle() {
    setError(null);
    setBusy(true);
    try {
      if (subscribed) {
        await unsubscribeFromPush();
        setSubscribed(false);
      } else {
        await subscribeToPush();
        setSubscribed(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Actie mislukt");
    } finally {
      setBusy(false);
    }
  }

  if (!supported || checking) return null;

  return (
    <div className="mb-4 flex items-center justify-between rounded-xl border border-gray-200 bg-white p-4">
      <div>
        <p className="font-medium">Pushmeldingen</p>
        <p className="text-sm text-gray-500">
          {subscribed
            ? "Je krijgt meldingen op dit toestel."
            : "Zet aan om meldingen op dit toestel te ontvangen, ook als de app dicht is."}
        </p>
        {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      </div>
      <button
        onClick={handleToggle}
        disabled={busy}
        className={`shrink-0 rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50 ${
          subscribed ? "bg-gray-100 text-gray-700 hover:bg-gray-200" : "bg-brand text-white hover:bg-brand-dark"
        }`}
      >
        {busy ? "Bezig..." : subscribed ? "Uitzetten" : "Aanzetten"}
      </button>
    </div>
  );
}
