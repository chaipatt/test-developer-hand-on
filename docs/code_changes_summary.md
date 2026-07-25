# `code_changes_summary.md` — Summary of Recent Additions & Updates

> Audience: an engineer picking up this repo cold. This document covers the
> **Backend Developer task** additions on top of the runnable baseline
> (`Binance TH order book → API → Postgres → API → BFF → frontend`). Everything
> below is evidenced by files in the repository; assumptions are labelled.

---

## 1. Scope of Changes

The change set adds a **second live data feed** — the Binance TH
`GET /api/v1/ticker/24hr` (24-hour rolling market statistics) — and threads it
through every layer of the existing vertical slice, mirroring how the baseline
already handles the order-book depth feed:

1. **Client** — a new method on the existing Binance HTTP client.
2. **Background worker** — the existing poll loop now also polls the ticker.
3. **Database** — a new migration (`000004_market_stats`) adds a table + two
   stored functions + an `updated_at` trigger.
4. **Repository** — two new methods on the repository Protocol and its Postgres
   implementation.
5. **API** — a new public endpoint `GET /market-stats/{symbol}`.
6. **BFF** — a new Next.js route handler proxying that endpoint.
7. **Frontend** — a new React widget rendered on the public home page.
8. **Tooling / docs / CI** — a golang-migrate before/after report program, a
   live "play with the API" quant script, UML docs, and a new CI job.

One **latent baseline bug** was also fixed (see §4).

---

## 2. New Capabilities

| Capability | Entry point | Notes |
| ---------- | ----------- | ----- |
| Fetch 24hr ticker from Binance TH | `OrderBookClient.get_ticker_24hr(symbol)` | Wraps failures in `BinanceClientError`. |
| Persist latest 24hr stats per symbol | `liqflow.upsert_market_stats(...)` stored function | One row per symbol (`ON CONFLICT (symbol) DO UPDATE`). |
| Background polling of ticker | `OrderbookPoller._poll_once` | Wrapped in `try/except`; a ticker failure never breaks the order-book loop. |
| Public REST endpoint | `GET /market-stats/{symbol}` | Returns `MarketStatsResponse`; `404` when no snapshot yet. |
| BFF proxy | `GET /api/market-stats/[symbol]` (Next.js) | Same public seam as the order-book routes. |
| Frontend widget | `MarketStatsWidget` | Polls every 3s via TanStack Query; rendered on `/`. |
| Migration before/after report | `tools/migration-report/main.go` | Uses `github.com/golang-migrate/migrate/v4/database/postgres` (a required task deliverable). |
| Live quant script | `api/scripts/play_ticker.py` | Cross-exchange (Binance TH vs Bitkub) THB ticker board. |
| Fetch Bitkub ticker + depth | `BitkubClient.get_ticker()` / `get_books(sym, lmt)` | New public client; wraps failures in `BitkubClientError`. |
| Admin cross-exchange comparison | `GET /admin/exchange-compare` | `Depends(require_admin)`; live Binance TH vs Bitkub for USDT/BTC/ETH-THB. |
| Admin exchange-compare widget | `ExchangeCompareWidget` + admin tabs | Polls every 5s via TanStack Query; 3 tables with spread + arbitrage. |

---

## 3. Modified vs. New Files

### New files

| File | Purpose |
| ---- | ------- |
| `db/000004_market_stats.up.sql` | Create `liqflow.market_stats` table, `updated_at` trigger, and `upsert_market_stats` / `get_latest_market_stats` stored functions. |
| `db/000004_market_stats.down.sql` | Drop the two functions and the table (reverse order). |
| `web/src/app/api/market-stats/[symbol]/route.ts` | BFF route handler proxying the API endpoint. |
| `web/src/app/api/market-stats/[symbol]/route.test.ts` | Vitest test for the BFF route. |
| `web/src/features/orderbook/components/market-stats.tsx` | `MarketStatsWidget` React component. |
| `tools/migration-report/main.go` (+ `go.mod` / `go.sum`) | golang-migrate before/after report program. |
| `api/scripts/play_ticker.py` | Live cross-exchange ticker board (Binance TH vs Bitkub). |
| `docs/design.md` | UML (component / sequence / ER) for this change. |
| `docs/migration-report.md` | How to run the report + captured output + interpretation. |
| `api/components/lf_tool/bitkub_client/{core,types,__init__}.py` | New Polylith component: public Bitkub market client. |
| `web/src/app/api/admin/exchange-compare/route.ts` (+ `route.test.ts`) | Admin-only BFF proxy for the comparison endpoint. |
| `web/src/features/admin/components/exchange-compare.tsx` | `ExchangeCompareWidget` (3 comparison tables). |

### Modified files

| File | What changed |
| ---- | ------------ |
| `api/components/lf_tool/binance_client/core.py` | Added `TICKER_24HR_ENDPOINT` + `get_ticker_24hr`. |
| `api/components/lf_tool/binance_client/types.py` | Added `Ticker24hr` TypedDict. |
| `api/components/lf_tool/binance_client/__init__.py` | Re-export `Ticker24hr`. |
| `api/components/lf_tool/orderbook_poller/core.py` | Added ticker polling branch (in `try/except`); **fixed bids/asks swap**. |
| `api/components/lf_tool/orderbook_repo/core.py` | Added `upsert_market_stats` / `get_latest_market_stats` to the Protocol. |
| `api/components/lf_tool/orderbook_repo/postgres.py` | Implemented both methods; added the two SQL constants. |
| `api/components/lf_tool/orderbook_repo/types.py` | Added `MarketStats` Pydantic model. |
| `api/components/lf_tool/orderbook_repo/__init__.py` | Re-export `MarketStats`. |
| `api/bases/lf_tool/liqflow_api/core.py` | Added `MarketStatsResponse` + `GET /market-stats/{symbol}`; added `ExchangeCompareResponse` + `GET /admin/exchange-compare` and its fetch/compare helpers. |
| `api/pyproject.toml`, `api/projects/liqflow_api/pyproject.toml` | Registered the `bitkub_client` brick. |
| `web/src/features/admin/{types,api,hooks}.ts` | Added exchange-compare zod schema, `fetchExchangeCompare`, `useExchangeCompare` (5s poll). |
| `web/src/app/(admin)/admin/page.tsx` | Tabbed layout: **Overview** (existing views) + **Exchange Compare**. |
| `web/src/features/orderbook/types.ts` | Added `marketStatsSchema` (zod) + `MarketStats` type. |
| `web/src/features/orderbook/api.ts` | Added `fetchMarketStats`. |
| `web/src/features/orderbook/hooks.ts` | Added `useMarketStats`. |
| `web/src/app/page.tsx` | Renders `<MarketStatsWidget symbol={DEFAULT_SYMBOL} />`. |
| `api/test/binance_client/test_client.py` | `test_get_ticker_24hr`. |
| `api/test/liqflow_api/test_api.py` | `test_market_stats_endpoint` + `FakeRepo.get_latest_market_stats`; `test_exchange_compare_requires_admin` + `test_exchange_compare_admin_ok`. |
| `api/test/orderbook_repo/test_integration.py` | `test_market_stats_upsert_and_get`. |
| `.forgejo/workflows/ci.yml` | New `db-integration` job. |
| `README.md` | "Backend task additions" section. |

---

## 4. Migration & Impact

### Database migration

- **New migration pair** `db/000004_market_stats.{up,down}.sql` (golang-migrate,
  applied by the `migrate` service in `compose.yaml`, or the migrate CLI).
- **New table** `liqflow.market_stats` — primary key `symbol`; all numeric
  fields stored as `TEXT` to preserve Binance's exact string precision (no float
  rounding). `ts` and `updated_at` are `TIMESTAMPTZ DEFAULT now()`.
- **New trigger** `trg_market_stats_set_updated_at` reuses the existing
  `liqflow.set_updated_at()` function (defined by an earlier baseline migration).
- **New stored functions** `upsert_market_stats(TEXT×8)` (plpgsql, upsert) and
  `get_latest_market_stats(TEXT)` (sql, `STABLE PARALLEL SAFE`), both
  `SECURITY INVOKER` with `SET search_path = liqflow, public`.
- **Reversibility verified** by `tools/migration-report` (`4 → 3 → 4`,
  `dirty=false` throughout). See `docs/migration-report.md`.

### Environment variables

- **No new required env vars.** The new feed reuses the existing
  `LIQFLOW_API_BINANCE_BASE_URL`, `LIQFLOW_API_SYMBOLS`, and
  `LIQFLOW_API_POLL_INTERVAL_SECONDS` (see `config.py` / `compose.yaml`).
- The migration report program reads a `DSN` env var (tooling only, not the
  runtime service).

### Breaking changes

- **None to existing endpoints or schemas.** All changes are additive:
  new table, new functions, new endpoint, new route, new widget. Existing
  order-book flow, auth, and RBAC are untouched.

### Bug fix (behavioural change to existing module)

In `api/components/lf_tool/orderbook_poller/core.py`, the baseline persisted the
order book with **bids and asks swapped**:

```python
# before (baseline, buggy):
bids=book.get("asks", []),
asks=book.get("bids", []),

# after (fixed):
bids=book.get("bids", []),
asks=book.get("asks", []),
```

Impact: the public top-of-book and full-depth views previously showed the ask
side as bids and vice-versa. After the fix, `best_bid`/`best_ask`/`spread` in
`GET /orderbook/{symbol}` are correct. This changes observable output of an
existing endpoint (a correctness fix, not an API contract change).

> **Assumption:** the swap was unintentional in the baseline — the exchange's
> `depth` payload keys `bids`/`asks` are authoritative and now map straight
> through.

---

## 5. Admin cross-exchange comparison (Binance TH vs Bitkub)

A second, self-contained change set: an **admin-only** live comparison feature,
added across all three layers without touching the DB.

- **New component** `bitkub_client` (Polylith brick, registered in both
  `pyproject.toml` files) — an `attrs` client over an injected `aiohttp` session,
  mirroring `binance_client`. `get_ticker()` fetches the whole Bitkub board
  (the ticker endpoint no longer accepts a `sym` filter — it returns error 99 —
  so callers index it by `THB_<base>`); `get_books(sym, lmt)` fetches depth;
  `to_bitkub_symbol("USDTTHB") -> "THB_USDT"`. Failures wrap in
  `BitkubClientError`.
- **New endpoint** `GET /admin/exchange-compare` (`Depends(require_admin)`) —
  fetches both exchanges concurrently (`asyncio.gather`) for `USDTTHB`,
  `BTCTHB`, `ETHTHB` over the shared `app.state.deps.session`, and returns, per
  pair, both exchanges' last / 24h change % / quote volume / best bid / best ask
  / spread %, plus `arbitrage_spread_pct` (Bitkub last vs Binance last). All
  numeric fields are `Decimal`-computed and emitted as fixed-point strings.
  Each exchange fetch is isolated (client wraps failures) → an `error` row on
  one side rather than a 500.
- **BFF + frontend** — `web/src/app/api/admin/exchange-compare/route.ts` proxies
  with the session token; `ExchangeCompareWidget` (under `features/admin/`)
  polls every 5s and renders three tables with coloured 24h change, spread, and
  a per-pair arbitrage line; `admin/page.tsx` gains an **Overview /
  Exchange Compare** tab bar.

**Impact:** no migration, no DB change, no new required env vars. The endpoint
makes live outbound calls to `https://api.binance.th` and `https://api.bitkub.com`
on each request (polled every 5s from the UI). Bitkub's `/books` outer rows can
be stale, so the ticker's `highestBid`/`lowestAsk` are used as the authoritative
top-of-book with the book rate as fallback. Additive only — no existing endpoint,
schema, or RBAC rule changed.

---

## 6. Security hardening & correctness fixes

### Outbound HTTP timeouts (resource-exhaustion harden)

The shared `aiohttp.ClientSession` (`deps.py`) was constructed with **no
timeout**. Every outbound exchange call — the background poller and the
5s-polled admin exchange-compare endpoint — could hang indefinitely on a stalled
upstream, tying up workers (a resource-exhaustion / DoS vector).

- Added `http_total_timeout_seconds` (default `10.0`) and
  `http_connect_timeout_seconds` (default `5.0`) to `LiqflowApiConfig`
  (env `LIQFLOW_API_HTTP_TOTAL_TIMEOUT_SECONDS` /
  `LIQFLOW_API_HTTP_CONNECT_TIMEOUT_SECONDS`).
- `deps.build_deps` now builds the session with an `aiohttp.ClientTimeout`.
- A timeout raises `asyncio.TimeoutError`, which is **not** an
  `aiohttp.ClientError`, so both `binance_client` and `bitkub_client` now catch
  it explicitly and wrap it in their `*ClientError` — preserving the
  "one hop fails → `error` row, not a 500" isolation of the compare endpoint.

### Zero-vs-missing display fix (money-math correctness)

`_fmt` in `liqflow_api/core.py` used `if not value: return None`, and the
`_spread_pct` / `_arbitrage_pct` guards used truthiness. `Decimal("0")` is falsy,
so a **legit zero** (flat 24h change, locked book with `bid==ask`, or exactly-flat
cross-exchange arbitrage) rendered as blank/`—`, conflating *"zero"* with
*"no data / error"*. Guards now test `is None` / `is not None`; genuine zeros
render as `"0"`, missing values stay `None`. The Bitkub `highestBid`/`lowestAsk`
`or`-fallback likewise no longer swallows a genuine `0` (uses an explicit
`None` check).
