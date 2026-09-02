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
