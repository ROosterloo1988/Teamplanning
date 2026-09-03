export type UserRole = "SPELER" | "CAPTAIN" | "BEHEER";

export type AvailabilityStatus = "AVAILABLE" | "UNAVAILABLE" | "IF_NEEDED" | "NO_RESPONSE";

export type MatchType = "COMPETITIE" | "BEKER" | "INHAAL" | "OVERIG";
export type MatchStatus = "GEPLAND" | "GESPEELD" | "AFGELAST";

export interface UserOut {
  id: number;
  naam: string;
  email: string;
  rol: UserRole;
  actief: boolean;
  player_id: number | null;
}

export interface TeamOut {
  id: number;
  naam: string;
  vereniging: string | null;
}

export interface PlayerOut {
  id: number;
  naam: string;
  team_id: number | null;
  user_id: number | null;
}

export interface MatchOut {
  id: number;
  external_id: string | null;
  season_id: number | null;
  type: MatchType;
  nummer: string | null;
  datum: string;
  tijd: string | null;
  thuisteam: string;
  uitteam: string;
  locatie: string | null;
  status: MatchStatus;
}

export interface AvailabilityOut {
  id: number;
  match_id: number;
  player_id: number;
  status: AvailabilityStatus;
  updated_at: string;
}

export interface AvailabilityWithPlayer extends AvailabilityOut {
  player_naam: string;
}

export interface LineupOut {
  id: number;
  match_id: number;
  published: boolean;
  published_at: string | null;
  player_ids: number[];
}

export interface DashboardStats {
  spelers: number;
  wedstrijden: number;
  wedstrijden_compleet: number;
  wedstrijden_missen_antwoorden: number;
}

export interface MatchReminderOut {
  match: MatchOut;
  total: number;
  missing: number;
}

export interface AuditLogOut {
  id: number;
  created_at: string;
  user_naam: string | null;
  entity_type: string;
  action: string;
  old_value: string | null;
  new_value: string | null;
  match_id: number | null;
  match_datum: string | null;
  match_thuisteam: string | null;
  match_uitteam: string | null;
  player_naam: string | null;
}

export interface PlayerStatsOut {
  player_id: number;
  player_naam: string;
  totaal: number;
  beschikbaar: number;
  niet_beschikbaar: number;
  indien_nodig: number;
  geen_antwoord: number;
  response_rate: number;
  keer_opgesteld: number;
}
