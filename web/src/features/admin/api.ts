import {
  adminUserSchema,
  exchangeCompareSchema,
  pollerStatusSchema,
  type AdminUser,
  type ExchangeCompare,
  type PollerStatus,
} from "./types";

export async function fetchUsers(): Promise<AdminUser[]> {
  const res = await fetch("/api/admin/users", { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`Failed to load users (${res.status})`);
  return z_array(adminUserSchema, await res.json());
}

export async function fetchPollerStatus(): Promise<PollerStatus> {
  const res = await fetch("/api/admin/poller-status", {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`Failed to load poller status (${res.status})`);
  return pollerStatusSchema.parse(await res.json());
}

export async function fetchExchangeCompare(): Promise<ExchangeCompare> {
  const res = await fetch("/api/admin/exchange-compare", {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string; error?: string }).detail ??
        (body as { error?: string }).error ??
        `Failed to load exchange comparison (${res.status})`,
    );
  }
  return exchangeCompareSchema.parse(await res.json());
}

// Small helper: parse an array of a schema without importing zod here directly.
function z_array<T>(schema: { parse: (v: unknown) => T }, data: unknown): T[] {
  if (!Array.isArray(data)) throw new Error("expected an array");
  return data.map((item) => schema.parse(item));
}
