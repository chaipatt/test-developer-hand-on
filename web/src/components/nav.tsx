"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useLogout, useMe } from "@/features/auth/hooks";

export function Nav() {
  const router = useRouter();
  const { data: me } = useMe();
  const logout = useLogout();

  return (
    <nav className="mb-6 flex flex-wrap items-center gap-4 border-b border-current pb-3 text-sm">
      <Link href="/" className="underline">
        Public book
      </Link>
      <Link href="/dashboard" className="underline">
        Dashboard
      </Link>
      <Link href="/admin" className="underline">
        Admin
      </Link>
      <span className="ml-auto font-mono">
        {me ? `${me.email} (${me.role})` : "not signed in"}
      </span>
      {me ? (
        <button
          type="button"
          className="border border-current px-2 py-0.5"
          onClick={() =>
            logout.mutate(undefined, {
              onSuccess: () => {
                router.push("/");
                router.refresh();
              },
            })
          }
        >
          Sign out
        </button>
      ) : (
        <Link href="/login" className="border border-current px-2 py-0.5">
          Sign in
        </Link>
      )}
    </nav>
  );
}
