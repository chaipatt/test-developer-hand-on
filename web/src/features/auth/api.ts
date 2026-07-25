import { principalSchema, type Principal } from "./types";

export async function login(email: string, password: string): Promise<{ role: string }> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string }).detail ?? "Login failed — check your credentials.",
    );
  }
  return res.json();
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
}

/** Returns the current principal, or null when not authenticated. */
export async function fetchMe(): Promise<Principal | null> {
  const res = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
  if (res.status === 401) return null;
  if (!res.ok) throw new Error(`Failed to load session (${res.status})`);
  return principalSchema.parse(await res.json());
}
