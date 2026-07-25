# Backend task — design & UML

Scope of this change: added the **Binance TH `GET /api/v1/ticker/24hr`** feed end
to end — new client method, poller wiring, `market_stats` table via migration
`000004`, a public API endpoint, BFF proxy, and a frontend widget.

## 1. Component / data-flow

```mermaid
flowchart LR
    BTH["Binance TH REST\n/api/v1/depth\n/api/v1/ticker/24hr"]
    subgraph API["Python API (FastAPI, Polylith)"]
        POLL["OrderbookPoller\n(background task)"]
        CLIENT["OrderBookClient\nget_orderbook / get_ticker_24hr"]
        REPO["PostgresOrderbookRepository"]
        EP["GET /market-stats/{symbol}\n(public)"]
    end
    DB[("Postgres\nliqflow schema\norderbook_snapshot\nmarket_stats")]
    BFF["Next.js BFF\n/api/market-stats/[symbol]"]
    UI["MarketStatsWidget\n(React 19)"]

    BTH --> CLIENT --> POLL --> REPO --> DB
    DB --> REPO --> EP --> BFF --> UI
```

New pieces are `get_ticker_24hr`, the poller's ticker branch, `market_stats`
(table + `upsert_market_stats` / `get_latest_market_stats` stored functions),
`/market-stats/{symbol}`, the BFF route, and the widget.

## 2. Poll → serve sequence

```mermaid
sequenceDiagram
    participant P as OrderbookPoller
    participant C as OrderBookClient
    participant B as Binance TH
    participant R as Repository
    participant D as Postgres
    participant F as Frontend
    participant BFF as Next.js BFF
    participant A as API

    loop every POLL_INTERVAL
        P->>C: get_ticker_24hr(symbol)
        C->>B: GET /api/v1/ticker/24hr?symbol=
        B-->>C: Ticker24hr JSON
        C-->>P: Ticker24hr
        P->>R: upsert_market_stats(...)
        R->>D: SELECT liqflow.upsert_market_stats($1..$8)
    end
    F->>BFF: GET /api/market-stats/USDTTHB
    BFF->>A: GET /market-stats/USDTTHB
    A->>R: get_latest_market_stats(symbol)
    R->>D: SELECT liqflow.get_latest_market_stats($1)
    D-->>A: row (or none → 404)
    A-->>BFF: MarketStatsResponse
    BFF-->>F: JSON (zod-validated)
```

Ticker polling is wrapped in try/except: a ticker failure logs a warning and
never breaks the order-book poll loop.

## 3. `market_stats` entity

```mermaid
erDiagram
    market_stats {
        text        symbol PK
        text        price_change
        text        price_change_pct
        text        last_price
        text        high_price
        text        low_price
        text        volume
        text        quote_volume
        timestamptz ts
        timestamptz updated_at
    }
```

One row per symbol (latest snapshot only — `ON CONFLICT (symbol) DO UPDATE`),
mirroring how the baseline keeps only the latest order-book snapshot. Numeric
fields are stored as `TEXT` to preserve Binance's exact string precision (no
float rounding); consumers parse to `Decimal` when doing math (see
`scripts/play_ticker.py`).

---

# Admin feature — cross-exchange comparison (Binance TH vs Bitkub)

A second change set: an **admin-only** live comparison. Unlike the market-stats
feature it does **not** persist — the endpoint fetches both exchanges live per
request and computes the metrics in-process. New pieces: the `bitkub_client`
component, `GET /admin/exchange-compare`, a BFF proxy, and `ExchangeCompareWidget`
under a tabbed admin page.

## 4. Component / data-flow

```mermaid
flowchart LR
    BTH["Binance TH REST\n/api/v1/ticker/24hr\n/api/v1/depth"]
    BKB["Bitkub REST\n/api/market/ticker\n/api/market/books"]
    subgraph API["Python API (FastAPI, Polylith)"]
        BC["OrderBookClient\n(binance_client)"]
        KC["BitkubClient\n(bitkub_client)"]
        EP["GET /admin/exchange-compare\n(admin — require_admin)"]
    end
    BFF["Next.js BFF\n/api/admin/exchange-compare\n(session token)"]
    UI["ExchangeCompareWidget\n(React 19, 5s poll)"]

    BTH --> BC --> EP
    BKB --> KC --> EP
    EP --> BFF --> UI
```

No database is involved: the endpoint gathers both exchanges concurrently and
returns computed metrics. Each exchange fetch is isolated so one side failing
yields an `error` row, not a 500.

## 5. Request → compare sequence

```mermaid
sequenceDiagram
    autonumber
    participant W as ExchangeCompareWidget
    participant BFF as Next.js BFF
    participant A as FastAPI (require_admin)
    participant BC as OrderBookClient
    participant KC as BitkubClient
    participant BN as Binance TH
    participant BK as Bitkub

    W->>BFF: GET /api/admin/exchange-compare (every 5s, cookie)
    BFF->>A: GET /admin/exchange-compare (Bearer token)
    Note over A: require_admin → 401/403 if not admin
    par per pair (USDT/BTC/ETH-THB), concurrently
        A->>BC: get_ticker_24hr + get(depth)
        BC->>BN: GET /api/v1/ticker/24hr, /api/v1/depth
        A->>KC: get_ticker + get_books
        KC->>BK: GET /api/market/ticker, /api/market/books
    end
    Note over A: Decimal math per pair then arbitrage spread. Error row when a side fails.
    A-->>BFF: 200 ExchangeCompareResponse
    BFF-->>W: JSON (zod-validated) → 3 tables
```

## 6. Response shape

`ExchangeCompareResponse { generated_at, pairs[] }` where each `pair` is
`{ symbol, binance: ExchangeQuote, bitkub: ExchangeQuote, arbitrage_spread_pct }`
and `ExchangeQuote` is `{ exchange, last_price, price_change_pct, quote_volume,
best_bid, best_ask, spread_pct, error? }`. All numeric fields are fixed-point
strings (Decimal-computed) or `null`. Bitkub best bid/ask come from the ticker's
`highestBid`/`lowestAsk` (authoritative; the `/books` outer rows can be stale),
with the book rate as fallback.
