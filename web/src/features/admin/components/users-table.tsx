"use client";

import { useAdminUsers } from "../hooks";

export function UsersTable() {
  const { data, isLoading, error } = useAdminUsers();

  if (isLoading) return <p>Loading users…</p>;
  if (error) return <p role="alert">Error: {(error as Error).message}</p>;

  return (
    <table className="border border-current text-sm">
      <thead>
        <tr>
          <th className="border border-current px-2 py-1 text-left">Email</th>
          <th className="border border-current px-2 py-1 text-left">Role</th>
          <th className="border border-current px-2 py-1 text-left">Active</th>
          <th className="border border-current px-2 py-1 text-left">Description</th>
        </tr>
      </thead>
      <tbody>
        {data?.map((u) => (
          <tr key={u.id}>
            <td className="border border-current px-2 py-1 font-mono">{u.email}</td>
            <td className="border border-current px-2 py-1">{u.role}</td>
            <td className="border border-current px-2 py-1">{u.is_active ? "yes" : "no"}</td>
            <td className="border border-current px-2 py-1">{u.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
