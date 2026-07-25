"use client";

import { useExchangeCompare } from "../hooks";
import type { ExchangeComparison, ExchangeQuote } from "../types";

// Group the integer part with thousands separators (444,444,555) while keeping
// the decimals verbatim — the values are exact-precision strings, so we never
// route them through Number (which would round).
function num(value: string | null | undefined): string {
  if (value == null || value === "") return "—";
  const neg = value.startsWith("-");
  const raw = neg ? value.slice(1) : value;
  const [intPart, decPart] = raw.split(".");
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const out = decPart != null ? `${grouped}.${decPart}` : grouped;
  return (neg ? "-" : "") + out;
}

/** Colour a signed percentage: green >= 0, red < 0, dim when absent. */
function ChangeCell({ value }: { value: string | null | undefined }) {
  if (value == null) return <span className="opacity-50">—</span>;
  const n = Number(value);
  const cls = Number.isNaN(n)
    ? ""
    : n >= 0
      ? "text-green-600 dark:text-green-400"
      : "text-red-600 dark:text-red-500";
  return (
    <span className={`font-mono ${cls}`}>
      {n >= 0 ? "+" : ""}
      {value}%
    </span>
  );
}

function QuoteRow({ q }: { q: ExchangeQuote }) {
  if (q.error) {
    return (
      <tr>
        <th className="border border-current px-2 py-1 text-left">{q.exchange}</th>
        <td className="border border-current px-2 py-1 text-red-600" colSpan={6}>
          ERR: {q.error}
        </td>
      </tr>
    );
  }
  return (
    <tr>
      <th className="border border-current px-2 py-1 text-left">{q.exchange}</th>
      <td className="border border-current px-2 py-1 font-mono text-right">
        {num(q.last_price)}
      </td>
      <td className="border border-current px-2 py-1 text-right">
        <ChangeCell value={q.price_change_pct} />
      </td>
      <td className="border border-current px-2 py-1 font-mono text-right">
        {num(q.quote_volume)}
      </td>
      <td className="border border-current px-2 py-1 font-mono text-right">
        {num(q.best_bid)}
      </td>
      <td className="border border-current px-2 py-1 font-mono text-right">
        {num(q.best_ask)}
      </td>
      <td className="border border-current px-2 py-1 font-mono text-right">
        {num(q.spread_pct)}%
      </td>
    </tr>
  );
}

function PairTable({ pair }: { pair: ExchangeComparison }) {
  const arb = pair.arbitrage_spread_pct;
  const arbN = arb == null ? NaN : Number(arb);
  const arbCls = Number.isNaN(arbN)
    ? ""
    : Math.abs(arbN) >= 0.1
      ? "text-green-600 dark:text-green-400"
      : "text-yellow-600 dark:text-yellow-400";
  const direction =
    Number.isNaN(arbN) || arbN === 0
      ? ""
      : arbN > 0
        ? "Bitkub above Binance"
        : "Binance above Bitkub";

  return (
    <section className="space-y-1">
      <h3 className="font-semibold text-md">{pair.symbol}</h3>
      <table className="border border-current text-sm w-full">
        <thead>
          <tr>
            <th className="border border-current px-2 py-1 text-left">Exchange</th>
            <th className="border border-current px-2 py-1 text-right">Last</th>
            <th className="border border-current px-2 py-1 text-right">24h Chg</th>
            <th className="border border-current px-2 py-1 text-right">Vol (THB)</th>
            <th className="border border-current px-2 py-1 text-right">Best Bid</th>
            <th className="border border-current px-2 py-1 text-right">Best Ask</th>
            <th className="border border-current px-2 py-1 text-right">Spread</th>
          </tr>
        </thead>
        <tbody>
          <QuoteRow q={pair.binance} />
          <QuoteRow q={pair.bitkub} />
        </tbody>
      </table>
      <p className="text-xs">
        <span className="font-semibold">Arbitrage spread:</span>{" "}
        {arb == null ? (
          <span className="opacity-50">n/a</span>
        ) : (
          <span className={`font-mono ${arbCls}`}>
            {arbN >= 0 ? "+" : ""}
            {arb}%
          </span>
        )}
        {direction && <span className="opacity-70"> ({direction}, last vs last)</span>}
      </p>
    </section>
  );
}

export function ExchangeCompareWidget() {
  const { data, isLoading, error, isFetching } = useExchangeCompare();

  if (isLoading) return <p>Loading exchange comparison…</p>;
  if (error)
    return <p role="alert">Exchange comparison error: {(error as Error).message}</p>;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <p className="text-xs opacity-70">
        Live Binance TH vs Bitkub · polling every 5s
        {isFetching ? " · updating…" : ""}
      </p>
      {data.pairs.map((pair) => (
        <PairTable key={pair.symbol} pair={pair} />
      ))}
    </div>
  );
}
