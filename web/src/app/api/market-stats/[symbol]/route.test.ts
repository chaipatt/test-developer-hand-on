import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";
import { NextRequest } from "next/server";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("GET /api/market-stats/[symbol]", () => {
  it("proxies request to backend and returns market stats JSON", async () => {
    const mockStats = {
      symbol: "USDTTHB",
      price_change: "0.10",
      price_change_pct: "0.30",
      last_price: "33.70",
      high_price: "34.00",
      low_price: "33.50",
      volume: "10000.0",
      quote_volume: "337000.0",
      ts: new Date().toISOString(),
    };

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      text: async () => JSON.stringify(mockStats),
    }));

    const req = new NextRequest("http://localhost:3000/api/market-stats/USDTTHB");
    const params = Promise.resolve({ symbol: "USDTTHB" });
    const res = await GET(req, { params });

    expect(res.status).toBe(200);
    const data = await res.json();
    expect(data.symbol).toBe("USDTTHB");
    expect(data.last_price).toBe("33.70");
  });
});
