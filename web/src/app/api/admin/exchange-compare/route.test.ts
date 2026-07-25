import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";
import { NextRequest } from "next/server";

afterEach(() => {
  vi.unstubAllGlobals();
});

function reqWithToken(token?: string): NextRequest {
  const url = "http://localhost:3000/api/admin/exchange-compare";
  return new NextRequest(
    url,
    token ? { headers: { cookie: `lf_session=${token}` } } : {},
  );
}

describe("GET /api/admin/exchange-compare", () => {
  it("returns 401 when no session cookie is present", async () => {
    const res = await GET(reqWithToken());
    expect(res.status).toBe(401);
  });

  it("proxies to backend with the bearer token and returns comparison JSON", async () => {
    const mock = {
      generated_at: new Date().toISOString(),
      pairs: [
        {
          symbol: "USDT/THB",
          binance: {
            exchange: "Binance TH",
            last_price: "33.66",
            price_change_pct: "0.10",
            quote_volume: "1000",
            best_bid: "33.65",
            best_ask: "33.67",
            spread_pct: "0.030",
            error: null,
          },
          bitkub: {
            exchange: "Bitkub",
            last_price: "33.64",
            price_change_pct: "0.05",
            quote_volume: "900",
            best_bid: "33.63",
            best_ask: "33.65",
            spread_pct: "0.030",
            error: null,
          },
          arbitrage_spread_pct: "-0.059",
        },
      ],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      headers: new Headers({ "content-type": "application/json" }),
      text: async () => JSON.stringify(mock),
    });
    vi.stubGlobal("fetch", fetchMock);

    const res = await GET(reqWithToken("admin-token"));
    expect(res.status).toBe(200);

    // token forwarded as a bearer header to the Python API
    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer admin-token");

    const data = await res.json();
    expect(data.pairs[0].symbol).toBe("USDT/THB");
    expect(data.pairs[0].arbitrage_spread_pct).toBe("-0.059");
  });
});
