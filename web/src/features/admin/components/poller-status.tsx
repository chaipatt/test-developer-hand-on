"use client";

import { usePollerStatus } from "../hooks";

export function PollerStatusCard() {
  const { data, isLoading, error } = usePollerStatus();

  if (isLoading) return <p>Loading poller status…</p>;
  if (error) return <p role="alert">Error: {(error as Error).message}</p>;
  if (!data) return null;

  const rows: [string, string][] = [
    ["Running", data.running ? "yes" : "no"],
    ["Symbols", data.symbols.join(", ")],
    ["Interval (s)", String(data.poll_interval_seconds ?? "—")],
    ["Poll count", String(data.poll_count ?? "—")],
    ["Last poll", data.last_poll_ts ?? "—"],
    ["Last error", data.last_error ?? "none"],
  ];

  return (
    <table className="border border-current text-sm">
      <tbody>
        {rows.map(([k, v]) => (
          <tr key={k}>
            <th className="border border-current px-2 py-1 text-left">{k}</th>
            <td className="border border-current px-2 py-1 font-mono">{v}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
