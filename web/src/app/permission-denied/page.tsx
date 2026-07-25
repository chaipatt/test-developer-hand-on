import Link from "next/link";

export default function PermissionDeniedPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Permission denied</h1>
      <p className="text-sm">
        Your account doesn’t have access to that page. Sign in with an account
        that has the required role, or head back to the public book.
      </p>
      <p className="text-sm">
        <Link href="/" className="underline">
          ← Public order book
        </Link>
      </p>
    </div>
  );
}
