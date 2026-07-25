import { NextRequest } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";

// Public: 24hr market stats. No session required.
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;
  const res = await backendFetch(`/market-stats/${encodeURIComponent(symbol)}`);
  return proxyJson(res);
}
