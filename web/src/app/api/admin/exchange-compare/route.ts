import { NextRequest, NextResponse } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";
import { SESSION_COOKIE } from "@/lib/auth/session";

// Admin-only: live Binance TH vs Bitkub comparison. Proxies to the Python API
// with the caller's session token; the backend enforces the admin role.
export async function GET(req: NextRequest) {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const res = await backendFetch("/admin/exchange-compare", { token });
  return proxyJson(res);
}
