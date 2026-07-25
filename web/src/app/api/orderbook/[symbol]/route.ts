import { NextRequest } from "next/server";

import { backendFetch, proxyJson } from "@/lib/api/backend";

// Public: top-of-book. No session required.
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await params;
  const res = await backendFetch(`/orderbook/${encodeURIComponent(symbol)}`);
  return proxyJson(res);
}
