const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const TOKEN_KEY = "teamplanning_token";
const TEAM_TOKEN_KEY = "teamplanning_team_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
}

// Teamtoken: bewijst dat het gedeelde teamwachtwoord is ingevoerd. Beschermt
// alleen de naam-kiezer (GET /auth/accounts, POST /auth/enter), niet de rest
// van de app — dat blijft het gewone token hierboven.
export function getTeamToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TEAM_TOKEN_KEY);
}

export function setTeamToken(token: string): void {
  window.localStorage.setItem(TEAM_TOKEN_KEY, token);
}

export function clearTeamToken(): void {
  window.localStorage.removeItem(TEAM_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  tokenOverride?: string | null
): Promise<T> {
  const token = tokenOverride !== undefined ? tokenOverride : getToken();
  const headers: Record<string, string> = {
    ...(options.body && !(options.body instanceof FormData)
      ? { "Content-Type": "application/json" }
      : {}),
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) {
    return undefined as T;
  }
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => apiFetch<T>(path),
  post: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, {
      method: "POST",
      body: body instanceof FormData ? body : body !== undefined ? JSON.stringify(body) : undefined,
    }),
  put: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "PUT", body: body !== undefined ? JSON.stringify(body) : undefined }),
};

// Team-gated calls voor de naam-kiezer: gebruiken expliciet het teamtoken
// in plaats van het (nog niet bestaande) gebruikerstoken.
export const teamApi = {
  get: <T>(path: string) => apiFetch<T>(path, {}, getTeamToken()),
  post: <T>(path: string, body?: unknown) =>
    apiFetch<T>(
      path,
      { method: "POST", body: body !== undefined ? JSON.stringify(body) : undefined },
      getTeamToken()
    ),
};
