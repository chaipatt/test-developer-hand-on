import { NextRequest, NextResponse } from "next/server";

import { BACKEND_API_BASE_URL } from "@/lib/api/backend";
import { SESSION_COOKIE, type Role } from "@/lib/auth/session";

// Staged RBAC gate (mirrors our production stack): public allowlist -> no session ->
// role check. Server-side checks in the Python API are authoritative; this is
// a cosmetic first line that also keeps unauthenticated users off gated pages.
//
// Path prefix -> minimum role required.
const PROTECTED_ROUTES: Record<string, Role> = {
  "/dashboard": "user",
  "/admin": "admin",
  "/api/admin": "admin",
};

function requiredRole(pathname: string): Role | undefined {
  for (const [prefix, role] of Object.entries(PROTECTED_ROUTES)) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      return role;
    }
  }
  return undefined;
}

async function fetchRole(token: string): Promise<Role | null> {
  try {
    const res = await fetch(`${BACKEND_API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    const body = (await res.json()) as { role?: Role };
    return body.role ?? null;
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const required = requiredRole(pathname);
  if (!required) {
    return NextResponse.next();
  }

  const isApi = pathname.startsWith("/api/");
  const deny = (status: number, error: string, redirectPath: string) => {
    if (isApi) {
      return NextResponse.json({ error }, { status });
    }
    return NextResponse.redirect(new URL(redirectPath, request.url));
  };

  const token = request.cookies.get(SESSION_COOKIE)?.value;
  if (!token) {
    return deny(401, "unauthenticated", "/login");
  }

  const role = await fetchRole(token);
  if (!role) {
    return deny(401, "unauthenticated", "/login");
  }

  //

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Run on everything except Next internals and static assets.
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico)$).*)",
  ],
};
