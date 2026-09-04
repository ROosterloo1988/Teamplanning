import { AvailabilityStatus } from "@/lib/types";

const LABELS: Record<AvailabilityStatus, string> = {
  AVAILABLE: "🟢 Kan",
  UNAVAILABLE: "🔴 Kan niet",
  IF_NEEDED: "🟡 Indien nodig",
  NO_RESPONSE: "⚪ Geen antwoord",
};

export function StatusBadge({ status }: { status: AvailabilityStatus }) {
  return <span>{LABELS[status]}</span>;
}

export function statusLabel(value: string | null): string {
  if (!value) return "—";
  return (LABELS as Record<string, string>)[value] ?? value;
}

export function daysUntil(datum: string): number {
  const target = new Date(datum + "T00:00:00");
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

export function formatMatchDate(datum: string): string {
  const date = new Date(datum + "T00:00:00");
  return date.toLocaleDateString("nl-NL", { weekday: "long", day: "numeric", month: "long" });
}

export function formatMatchDateShort(datum: string): string {
  const date = new Date(datum + "T00:00:00");
  return date.toLocaleDateString("nl-NL", { day: "numeric", month: "short" });
}

export function mapsUrl(locatie: string): string {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(locatie)}`;
}

// Locatie als tikbare Google Maps-link — werkt met een volledig adres of
// alleen een zaalnaam, zodat je er meteen mee kunt navigeren.
export function LocatieLink({ locatie }: { locatie: string | null }) {
  if (!locatie) return null;
  return (
    <a
      href={mapsUrl(locatie)}
      target="_blank"
      rel="noopener noreferrer"
      className="text-brand hover:underline"
      onClick={(e) => e.stopPropagation()}
    >
      📍 {locatie}
    </a>
  );
}
