"use client";

import { useMarketStats } from "../hooks";

export function MarketStatsWidget({ symbol }: { symbol: string }) {
  const { data, isLoading, error } = useMarketStats(symbol);

  if (isLoading) return <p>Loading 24hr market stats…</p>;
  if (error) return <p role="alert">Market stats error: {(error as Error).message}</p>;
  if (!data) return null;

  return (
    <section className="space-y-2 border border-current p-3 my-4">
      <h3 className="font-semibold text-md">Binance TH 24hr Market Stats ({data.symbol})</h3>
      <table className="border border-current text-sm w-full">
        <tbody>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Last Price</th>
            <td className="border border-current px-2 py-1 font-mono">{data.last_price}</td>
            <th className="border border-current px-2 py-1 text-left">Price Change (%)</th>
            <td className="border border-current px-2 py-1 font-mono">
              {data.price_change} ({data.price_change_pct}%)
            </td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">24h High</th>
            <td className="border border-current px-2 py-1 font-mono">{data.high_price}</td>
            <th className="border border-current px-2 py-1 text-left">24h Low</th>
            <td className="border border-current px-2 py-1 font-mono">{data.low_price}</td>
          </tr>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Volume</th>
            <td className="border border-current px-2 py-1 font-mono">{data.volume}</td>
            <th className="border border-current px-2 py-1 text-left">Quote Volume</th>
            <td className="border border-current px-2 py-1 font-mono">{data.quote_volume}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
