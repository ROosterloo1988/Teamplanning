import { AuditLogOut } from "@/lib/types";
import { statusLabel } from "@/components/StatusBadge";

function formatTimestamp(iso: string): string {
  return new Date(iso).toLocaleString("nl-NL", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function describe(entry: AuditLogOut): { title: string; change: string | null } {
  const wie = entry.user_naam ?? entry.player_naam ?? "Iemand";
  const wedstrijd =
    entry.match_thuisteam && entry.match_uitteam
      ? `${entry.match_thuisteam} - ${entry.match_uitteam}`
      : null;

  if (entry.entity_type === "availability") {
    const title = `${entry.player_naam ?? wie} wijzigde beschikbaarheid${
      wedstrijd ? ` voor ${wedstrijd}` : ""
    }`;
    const change = `${statusLabel(entry.old_value)} → ${statusLabel(entry.new_value)}`;
    return { title, change };
  }

  if (entry.entity_type === "lineup") {
    const actie = entry.action === "publish" ? "publiceerde de opstelling" : "wijzigde de opstelling";
    const title = `${wie} ${actie}${wedstrijd ? ` voor ${wedstrijd}` : ""}`;
    const change =
      entry.action === "publish"
        ? entry.new_value
          ? `Opgesteld: ${entry.new_value}`
          : null
        : `${entry.old_value || "niemand"} → ${entry.new_value || "niemand"}`;
    return { title, change };
  }

  return { title: `${wie} — ${entry.action}`, change: null };
}

export function AuditLogList({ entries }: { entries: AuditLogOut[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-gray-400">Geen wijzigingen gevonden.</p>;
  }

  return (
    <ul className="divide-y divide-gray-100 rounded-xl border border-gray-200 bg-white">
      {entries.map((entry) => {
        const { title, change } = describe(entry);
        return (
          <li key={entry.id} className="px-4 py-3 text-sm">
            <p className="font-medium text-gray-800">{title}</p>
            <p className="text-xs text-gray-400">{formatTimestamp(entry.created_at)}</p>
            {change && <p className="mt-1 text-gray-600">{change}</p>}
          </li>
        );
      })}
    </ul>
  );
}
