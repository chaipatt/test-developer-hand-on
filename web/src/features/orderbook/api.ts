// Client-side calls hit the BFF (/api/*), never the Python API directly.
import {
  fullBookSchema,
  marketStatsSchema,
  topOfBookSchema,
  type FullBook,
  type MarketStats,
  type TopOfBook,
} from "./types";

async function getJson(path: string): Promise<unknown> {
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(
      (body as { detail?: string; error?: string }).detail ??
        (body as { error?: string }).error ??
        `Request failed (${res.status})`,
    );
  }
  return res.json();
}

export async function fetchTopOfBook(symbol: string): Promise<TopOfBook> {
  const data = await getJson(`/api/orderbook/${encodeURIComponent(symbol)}`);
  return topOfBookSchema.parse(data);
}

export async function fetchFullBook(symbol: string): Promise<FullBook> {
  const data = await getJson(`/api/orderbook/${encodeURIComponent(symbol)}/full`);
  return fullBookSchema.parse(data);
}

export async function fetchMarketStats(symbol: string): Promise<MarketStats> {
  const data = await getJson(`/api/market-stats/${encodeURIComponent(symbol)}`);
  return marketStatsSchema.parse(data);
}

