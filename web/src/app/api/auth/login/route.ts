import { NextRequest, NextResponse } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";
import { SESSION_COOKIE } from "@/lib/auth/session";

const SESSION_MAX_AGE = 60 * 60 * 12; // 12h, matches the backend JWT default.

export async function POST(req: NextRequest) {
  const body = await req.json();
  const res = await backendFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    return proxyJson(res);
  }

  const data = (await res.json()) as { access_token: string; role: string };
  const response = NextResponse.json({ role: data.role });
  // Store the JWT in an httpOnly cookie so client JS can't read it.
  response.cookies.set(SESSION_COOKIE, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    secure: process.env.NODE_ENV === "production",
    maxAge: SESSION_MAX_AGE,
  });
  return response;
}
