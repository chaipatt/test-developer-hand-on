import { NextRequest, NextResponse } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";
import { SESSION_COOKIE } from "@/lib/auth/session";

// User: full depth. Requires a session; the backend re-checks the role.
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const { symbol } = await params;
  const res = await backendFetch(
    `/orderbook/${encodeURIComponent(symbol)}/full`,
    { token },
  );
  return proxyJson(res);
}
