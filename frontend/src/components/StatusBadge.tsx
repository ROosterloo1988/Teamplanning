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

export function formatMatchDate(datum: string): string {
  const date = new Date(datum + "T00:00:00");
  return date.toLocaleDateString("nl-NL", { weekday: "long", day: "numeric", month: "long" });
}

export function formatMatchDateShort(datum: string): string {
  const date = new Date(datum + "T00:00:00");
  return date.toLocaleDateString("nl-NL", { day: "numeric", month: "short" });
}
