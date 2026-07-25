"use client";

import { useTopOfBook } from "../hooks";
import { DepthTable } from "./depth-table";

export function TopOfBook({ symbol }: { symbol: string }) {
  const { data, isLoading, error } = useTopOfBook(symbol);

  if (isLoading) return <p>Loading order book…</p>;
  if (error) return <p role="alert">Error: {(error as Error).message}</p>;
  if (!data) return <p>No data yet for {symbol}.</p>;

  return (
    <section className="space-y-3">
      <table className="border border-current text-sm">
        <tbody>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Symbol</th>
            <td className="border border-current px-2 py-1 font-mono">{data.symbol}</td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Best bid</th>
            <td className="border border-current px-2 py-1 font-mono">
              {data.best_bid ? `${data.best_bid[0]} × ${data.best_bid[1]}` : "—"}
            </td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Best ask</th>
            <td className="border border-current px-2 py-1 font-mono">
              {data.best_ask ? `${data.best_ask[0]} × ${data.best_ask[1]}` : "—"}
            </td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Spread</th>
            <td className="border border-current px-2 py-1 font-mono">{data.spread ?? "—"}</td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Snapshot</th>
            <td className="border border-current px-2 py-1 font-mono">{data.ts}</td>
          </tr>
        </tbody>
      </table>

      <div className="flex flex-wrap gap-6">
        <DepthTable title="Bids (preview)" levels={data.bids} />
        <DepthTable title="Asks (preview)" levels={data.asks} />
      </div>
    </section>
  );
}
