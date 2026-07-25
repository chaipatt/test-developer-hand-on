// Single seam between the BFF (Next route handlers + middleware) and the
// Python API. The frontend never calls the Python API directly — everything
// goes through the BFF via this wrapper (same pattern as our production stack,
// minus the HMAC request signing).
import { NextResponse } from "next/server";

export const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL ?? "http://localhost:8000";

type BackendInit = RequestInit & { token?: string | null };

/** Fetch the Python API, attaching a Bearer token when provided. */
export async function backendFetch(
  path: string,
  init: BackendInit = {},
): Promise<Response> {
  const { token, headers, ...rest } = init;
  const mergedHeaders = new Headers(headers);
  mergedHeaders.set("Accept", "application/json");
  if (token) {
    mergedHeaders.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${BACKEND_API_BASE_URL}${path}`, {
    cache: "no-store",
    ...rest,
    headers: mergedHeaders,
  });
}

/** Forward a backend Response through the BFF, preserving status + JSON body. */
export async function proxyJson(res: Response): Promise<NextResponse> {
  let body: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = { detail: text };
    }
  }
  return NextResponse.json(body, { status: res.status });
}
