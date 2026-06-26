const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
}

export function getAuthHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export function getRole(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("role");
}

export function isAdmin(): boolean {
  return getRole() === "admin";
}

export function isSafetyEngineer(): boolean {
  return getRole() === "safety_engineer";
}

export function isManager(): boolean {
  return getRole() === "manager";
}

export function decodeRole(token: string): string {
  try {
    const payloadPart = token.split(".")[1];
    const padded = payloadPart.padEnd(payloadPart.length + (4 - payloadPart.length % 4) % 4, "=");
    const payload = JSON.parse(atob(padded.replace(/-/g, "+").replace(/_/g, "/")));
    return payload.role ?? "worker";
  } catch {
    return "worker";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
      ...options.headers,
    },
  });

  if (res.status === 401 && !path.endsWith("/auth/login")) {
    clearSession();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Ошибка запроса");
  }

  if (res.status === 204) return null as T;
  return res.json();
}

export const api = {
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),

  get: <T>(path: string) => request<T>(path),

  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),

  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),

  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  postForm: <T>(path: string, formData: FormData) => {
    return fetch(`${BASE_URL}${path}`, {
      method: "POST",
      credentials: "include",
      headers: getAuthHeaders(),
      body: formData,
    }).then(async (res) => {
      if (res.status === 401) {
        clearSession();
        window.location.href = "/login";
        throw new Error("Unauthorized");
      }
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? "Ошибка запроса");
      }
      return res.json() as Promise<T>;
    });
  },
};
