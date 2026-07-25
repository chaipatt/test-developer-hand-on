import { NextRequest, NextResponse } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";
import { SESSION_COOKIE } from "@/lib/auth/session";

export async function GET(req: NextRequest) {
  const token = req.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return NextResponse.json({ error: "unauthenticated" }, { status: 401 });
  }
  const res = await backendFetch("/admin/poller-status", { token });
  return proxyJson(res);
}
