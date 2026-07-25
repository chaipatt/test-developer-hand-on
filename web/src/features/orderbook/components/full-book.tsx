"use client";

import { useFullBook } from "../hooks";
import { DepthTable } from "./depth-table";

export function FullBook({ symbol }: { symbol: string }) {
  const { data, isLoading, error } = useFullBook(symbol);

  if (isLoading) return <p>Loading full depth…</p>;
  if (error) return <p role="alert">Error: {(error as Error).message}</p>;
  if (!data) return <p>No data yet for {symbol}.</p>;

  return (
    <section className="space-y-3">
      <p className="font-mono text-sm">
        {data.symbol} · lastUpdateId {data.last_update_id ?? "—"} · {data.ts}
      </p>
      <div className="flex flex-wrap gap-6">
        <DepthTable title={`Bids (${data.bids.length})`} levels={data.bids} />
        <DepthTable title={`Asks (${data.asks.length})`} levels={data.asks} />
      </div>
    </section>
  );
}
