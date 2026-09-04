export type UserRole = "SPELER" | "CAPTAIN" | "BEHEER";

export type AvailabilityStatus = "AVAILABLE" | "UNAVAILABLE" | "IF_NEEDED" | "NO_RESPONSE";

export type MatchType = "COMPETITIE" | "BEKER" | "INHAAL" | "OVERIG";
export type MatchStatus = "GEPLAND" | "GESPEELD" | "AFGELAST";

export interface AccountOption {
  id: number;
  naam: string;
  rol: UserRole;
}

export interface UserOut {
  id: number;
  naam: string;
  email: string | null;
  rol: UserRole;
  actief: boolean;
  player_id: number | null;
}

export interface PlayerOut {
  id: number;
  naam: string;
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
  player_naam: string[];
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

export interface SeasonOut {
  id: number;
  naam: string;
  startjaar: number;
  eindjaar: number;
  actief: boolean;
}

export interface NotificationOut {
  id: number;
  type: string;
  title: string;
  body: string | null;
  match_id: number | null;
  created_at: string;
  read_at: string | null;
}

export interface TeambeheerConfigOut {
  id: number;
  season_id: number;
  bond_id: number;
  poule: string;
  team_id: number;
  team_naam: string | null;
  last_synced_at: string | null;
  last_sync_status: string | null;
  last_sync_message: string | null;
}

export type TeambeheerFixtureStatus = "nieuw" | "bestaand" | "geen_datum";

export interface TeambeheerFixturePreview {
  speelweek: number;
  datum: string | null;
  datum_raw: string;
  thuisteam: string;
  uitteam: string;
  status: TeambeheerFixtureStatus;
}

export interface TeambeheerSyncResult {
  created: number;
  updated: number;
  unchanged: number;
  skipped_no_date: number;
  team_naam: string | null;
}
