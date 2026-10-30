"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import {
  SeasonOut,
  TeambeheerConfigOut,
  TeambeheerFixturePreview,
  TeambeheerSyncResult,
  TeamFeedDiagnosticsOut,
} from "@/lib/types";
import { Nav } from "@/components/Nav";
import { BeheerNav } from "@/components/BeheerNav";
import { LocatieLink } from "@/components/StatusBadge";

const STATUS_LABELS: Record<string, string> = {
  nieuw: "🆕 Nieuw",
  bestaand: "✅ Bestaand",
  geen_datum: "⚪ Datum nog niet bekend",
};

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("nl-NL", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function BeheerTeambeheerPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [seasons, setSeasons] = useState<SeasonOut[]>([]);
  const [seasonId, setSeasonId] = useState<number | null>(null);
  const [config, setConfig] = useState<TeambeheerConfigOut | null>(null);
  const [form, setForm] = useState({ bond_id: "11", poule: "", team_id: "" });
  const [preview, setPreview] = useState<TeambeheerFixturePreview[] | null>(null);
  const [syncResult, setSyncResult] = useState<TeambeheerSyncResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingConfig, setSavingConfig] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [fetching, setFetching] = useState(true);
  const [feedTest, setFeedTest] = useState<TeamFeedDiagnosticsOut | null>(null);
  const [feedTestError, setFeedTestError] = useState<string | null>(null);
  const [feedTesting, setFeedTesting] = useState(false);

  const loadConfig = useCallback(async (sid: number) => {
    setPreview(null);
    setSyncResult(null);
    setError(null);
    setFeedTest(null);
    setFeedTestError(null);
    try {
      const data = await api.get<TeambeheerConfigOut>(`/teambeheer/config/${sid}`);
      setConfig(data);
      setForm({ bond_id: String(data.bond_id), poule: data.poule, team_id: String(data.team_id) });
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setConfig(null);
        setForm({ bond_id: "11", poule: "", team_id: "" });
      } else {
        throw err;
      }
    }
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
    api
      .get<SeasonOut[]>("/seasons")
      .then(async (seasonsData) => {
        setSeasons(seasonsData);
        const active = seasonsData.find((s) => s.actief) ?? seasonsData[0];
        if (active) {
          setSeasonId(active.id);
          await loadConfig(active.id);
        }
      })
      .finally(() => setFetching(false));
  }, [user, loading, router, loadConfig]);

  async function handleSeasonChange(value: string) {
    const sid = Number(value);
    setSeasonId(sid);
    await loadConfig(sid);
  }

  async function handleSaveConfig(e: React.FormEvent) {
    e.preventDefault();
    if (!seasonId) return;
    setError(null);
    setSavingConfig(true);
    try {
      const updated = await api.put<TeambeheerConfigOut>(`/teambeheer/config/${seasonId}`, {
        bond_id: Number(form.bond_id),
        poule: form.poule,
        team_id: Number(form.team_id),
      });
      setConfig(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Opslaan mislukt");
    } finally {
      setSavingConfig(false);
    }
  }

  async function handlePreview() {
    if (!seasonId) return;
    setError(null);
    setSyncResult(null);
    setLoadingPreview(true);
    try {
      const data = await api.get<TeambeheerFixturePreview[]>(`/teambeheer/preview/${seasonId}`);
      setPreview(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Ophalen mislukt");
    } finally {
      setLoadingPreview(false);
    }
  }

  async function handleFeedTest() {
    if (!seasonId) return;
    setFeedTestError(null);
    setFeedTesting(true);
    try {
      const data = await api.get<TeamFeedDiagnosticsOut>(`/teambeheer/team-feed-test/${seasonId}`);
      setFeedTest(data);
    } catch (err) {
      setFeedTestError(err instanceof ApiError ? err.message : "Testen mislukt");
    } finally {
      setFeedTesting(false);
    }
  }

  async function handleSync() {
    if (!seasonId) return;
    setError(null);
    setSyncing(true);
    try {
      const result = await api.post<TeambeheerSyncResult>(`/teambeheer/sync/${seasonId}`);
      setSyncResult(result);
      await loadConfig(seasonId);
      await handlePreview();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Importeren mislukt");
    } finally {
      setSyncing(false);
    }
  }

  if (loading || fetching) return <div className="py-10 text-center text-gray-400">Laden...</div>;

  return (
    <div>
      <Nav />
      <BeheerNav />
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Teambeheer</h1>
        <select
          value={seasonId ?? ""}
          onChange={(e) => handleSeasonChange(e.target.value)}
          className="rounded-lg border border-gray-300 px-3 py-1.5 text-sm"
        >
          {seasons.map((s) => (
            <option key={s.id} value={s.id}>
              {s.naam}
              {s.actief ? " (actief)" : ""}
            </option>
          ))}
        </select>
      </div>
      <p className="mb-6 text-gray-500">
        Koppel dit seizoen aan de Teambeheer SDC jaarprogramma-feed. De app haalt hiermee
        automatisch elke nacht nieuwe of gewijzigde wedstrijden op.
      </p>

      <h2 className="mb-3 font-medium">Koppeling</h2>
      <form
        onSubmit={handleSaveConfig}
        className="mb-6 space-y-3 rounded-xl border border-gray-200 bg-white p-4"
      >
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Bond (d=)</label>
          <input
            type="number"
            required
            value={form.bond_id}
            onChange={(e) => setForm({ ...form, bond_id: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Poule (div=)</label>
          <input
            placeholder="bv. 1A"
            required
            value={form.poule}
            onChange={(e) => setForm({ ...form, poule: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Teamnummer (t=, uit de team-URL)
          </label>
          <input
            type="number"
            required
            value={form.team_id}
            onChange={(e) => setForm({ ...form, team_id: e.target.value })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2"
          />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={savingConfig}
          className="w-full rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
        >
          {savingConfig ? "Bezig..." : "Koppeling opslaan"}
        </button>
      </form>

      {config && (
        <div className="mb-6 rounded-xl border border-gray-200 bg-white p-4 text-sm">
          {config.team_naam && (
            <p className="mb-1">
              Gekoppeld team: <span className="font-medium">{config.team_naam}</span>
            </p>
          )}
          {config.last_synced_at ? (
            <p className="text-gray-500">
              Laatste sync: {formatTimestamp(config.last_synced_at)}
              {config.last_sync_status === "error" ? " — ⚠️ mislukt" : ""}
            </p>
          ) : (
            <p className="text-gray-400">Nog niet eerder gesynchroniseerd.</p>
          )}
          {config.last_sync_message && (
            <p className="mt-1 text-gray-500">{config.last_sync_message}</p>
          )}
        </div>
      )}

      {config && (
        <>
          <div className="mb-3 flex gap-3">
            <button
              onClick={handlePreview}
              disabled={loadingPreview}
              className="flex-1 rounded-lg border border-gray-300 py-2 font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
            >
              {loadingPreview ? "Bezig..." : "Wedstrijden ophalen"}
            </button>
            <button
              onClick={handleSync}
              disabled={syncing}
              className="flex-1 rounded-lg bg-brand py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
            >
              {syncing ? "Bezig..." : "Wedstrijden importeren"}
            </button>
          </div>

          {syncResult && (
            <div className="mb-4 rounded-lg bg-green-50 p-3 text-sm text-green-800">
              ✅ {syncResult.created} nieuw, {syncResult.updated} gewijzigd, {syncResult.unchanged}{" "}
              ongewijzigd
              {syncResult.skipped_no_date > 0 &&
                `, ${syncResult.skipped_no_date} nog zonder datum overgeslagen`}
              .
            </div>
          )}

          {preview && (
            <table className="w-full overflow-hidden rounded-xl border border-gray-200 bg-white text-sm">
              <thead className="bg-gray-50 text-left text-gray-500">
                <tr>
                  <th className="px-3 py-2 font-medium">Week</th>
                  <th className="px-3 py-2 font-medium">Datum</th>
                  <th className="px-3 py-2 font-medium">Thuis</th>
                  <th className="px-3 py-2 font-medium">Uit</th>
                  <th className="px-3 py-2 font-medium">Locatie</th>
                  <th className="px-3 py-2 font-medium">Uitslag</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.map((f, idx) => (
                  <tr key={idx}>
                    <td className="px-3 py-2">{f.speelweek}</td>
                    <td className="px-3 py-2">{f.datum ?? f.datum_raw}</td>
                    <td className="px-3 py-2">{f.thuisteam}</td>
                    <td className="px-3 py-2">{f.uitteam}</td>
                    <td className="px-3 py-2">
                      {f.locatie ? <LocatieLink locatie={f.locatie} /> : "—"}
                    </td>
                    <td className="px-3 py-2">
                      {f.uitslag ? (
                        f.uitslag_url ? (
                          <a
                            href={f.uitslag_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-brand hover:underline"
                          >
                            {f.uitslag}
                          </a>
                        ) : (
                          f.uitslag
                        )
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-2">{STATUS_LABELS[f.status] ?? f.status}</td>
                  </tr>
                ))}
                {preview.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-3 py-6 text-center text-gray-400">
                      Geen wedstrijden gevonden voor dit team in deze poule
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}

          <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <h2 className="mb-1 font-medium text-amber-900">🧪 Beta: nieuwe feed testen</h2>
            <p className="mb-3 text-sm text-amber-800">
              Probeert de alternatieve Teambeheer-feed (per team, inclusief bekerwedstrijden) uit.
              Slaat niets op — alleen bedoeld om te testen of deze op de echte server werkt,
              voordat we 'm eventueel samenvoegen met de echte sync hierboven.
            </p>
            <button
              onClick={handleFeedTest}
              disabled={feedTesting}
              className="rounded-lg border border-amber-400 bg-white px-4 py-2 text-sm font-medium text-amber-900 hover:bg-amber-100 disabled:opacity-50"
            >
              {feedTesting ? "Bezig..." : "Nieuwe feed testen"}
            </button>

            {feedTestError && <p className="mt-3 text-sm text-red-600">{feedTestError}</p>}

            {feedTest && (
              <div className="mt-4 space-y-3 text-sm">
                <p className="break-all text-amber-800">
                  <span className="font-medium">URL:</span> {feedTest.url}
                </p>
                {feedTest.error ? (
                  <p className="text-red-600">⚠️ Ophalen mislukt: {feedTest.error}</p>
                ) : (
                  <ul className="grid grid-cols-2 gap-1 text-amber-900 sm:grid-cols-4">
                    <li>HTML: {feedTest.html_length} tekens</li>
                    <li>"computer"-blok: {feedTest.computer_section_found ? "✅" : "❌"}</li>
                    <li>"Wedstrijden"-kop: {feedTest.wedstrijden_header_found ? "✅" : "❌"}</li>
                    <li>Tabel: {feedTest.table_found ? "✅" : "❌"}</li>
                    <li>Rijen gevonden: {feedTest.raw_row_count}</li>
                    <li>Overgeslagen (vrije week): {feedTest.skipped_vrije_week}</li>
                    <li>Overgeslagen (geen id): {feedTest.skipped_no_title}</li>
                    <li className="font-medium">Geparst: {feedTest.parsed_count}</li>
                  </ul>
                )}

                {feedTest.fixtures.length > 0 && (
                  <table className="w-full overflow-hidden rounded-lg border border-amber-200 bg-white">
                    <thead className="bg-amber-100 text-left text-amber-900">
                      <tr>
                        <th className="px-3 py-2 font-medium">Ronde</th>
                        <th className="px-3 py-2 font-medium">Datum</th>
                        <th className="px-3 py-2 font-medium">Thuis</th>
                        <th className="px-3 py-2 font-medium">Uit</th>
                        <th className="px-3 py-2 font-medium">Uitslag</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-amber-100">
                      {feedTest.fixtures.map((f, idx) => (
                        <tr key={idx}>
                          <td className="px-3 py-2">
                            {f.ronde}
                            {f.is_beker && " 🏆"}
                          </td>
                          <td className="px-3 py-2">{f.datum ?? f.datum_raw}</td>
                          <td className="px-3 py-2">{f.thuisteam}</td>
                          <td className="px-3 py-2">{f.uitteam}</td>
                          <td className="px-3 py-2">{f.uitslag ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
