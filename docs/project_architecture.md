# `project_architecture.md` — Architecture & Execution Flow

> Audience: an incoming engineer who needs the system's shape, how a request
> flows through it, where each responsibility lives, and how to run/extend it.
> All names and paths are real; assumptions are labelled.

---

## 1. High-Level Overview

The repo is a single **vertical slice** in a **layered / Backend-for-Frontend
(BFF)** style:

```
Binance TH REST  →  Python API (poller + repo + FastAPI)  →  Postgres
                                     ▲
                                     │ (server-side only)
                              Next.js BFF  →  React frontend  →  browser
```

Key architectural properties:

- **Clean layering inside the API** (Polylith): `bases/` (the app/composition
  root) depends on `components/` (client, poller, repo, auth), and the repo hides
  Postgres behind a `Protocol` + stored functions.
- **BFF pattern in the web tier**: the browser only ever talks to Next.js
  (`/api/*`); Next.js is the *only* thing that talks to the Python API. The seam
  is `web/src/lib/api/backend.ts`.
- **Event-ish background worker**: an in-process `asyncio` poll loop drives
  ingestion on a fixed interval.

### Component diagram

```mermaid
graph TD
    subgraph EXT[External]
        BTH["Binance TH REST\n/api/v1/depth\n/api/v1/ticker/24hr"]
        BKB["Bitkub REST\n/api/market/ticker\n/api/market/books"]
    end

    subgraph API["Python API (FastAPI · Polylith · port 8000)"]
        POLL["OrderbookPoller\n(asyncio background task)"]
        CLIENT["OrderBookClient\nget / get_ticker_24hr"]
        KCLIENT["BitkubClient\nget_ticker / get_books"]
        REPO["PostgresOrderbookRepository\n(Protocol seam)"]
        EPPUB["GET /orderbook/{symbol}\nGET /market-stats/{symbol}  (public)"]
        EPUSER["GET /orderbook/{symbol}/full  (user)"]
        EPADMIN["GET /admin/*  · GET /admin/exchange-compare  (admin)"]
        AUTH["auth: JWT + RBAC deps"]
    end

    DB[("Postgres 16\nliqflow schema\norderbook_snapshot · market_stats · users")]

    subgraph WEB["Next.js 15 (frontend + BFF · port 3000)"]
        BFF["Route handlers /api/*\nbackendFetch / proxyJson"]
        MW["middleware (session / RBAC mirror)"]
        UI["React 19 components\nMarketStatsWidget · TopOfBook · ExchangeCompareWidget"]
    end

    BROWSER(["Browser"])

    BTH --> CLIENT --> POLL --> REPO --> DB
    DB --> REPO --> EPPUB
    BTH --> CLIENT --> EPADMIN
    BKB --> KCLIENT --> EPADMIN
    EPUSER --- AUTH
    EPADMIN --- AUTH
    BROWSER --> UI --> BFF --> EPPUB
    BFF --> EPUSER
    BFF --> EPADMIN
    MW --- BFF
```

---

## 2. Detailed Execution Flow

### End-to-end trace (market-stats read)

`Browser → React hook → BFF route handler → backend seam → FastAPI handler →
Repository → stored function → Postgres`, then back up the same chain with zod
validation at the BFF-consumer boundary.

Concretely:

1. `page.tsx` renders `MarketStatsWidget` →
   `useMarketStats("USDTTHB")` (`web/src/features/orderbook/hooks.ts`).
2. `fetchMarketStats` (`api.ts`) → `GET /api/market-stats/USDTTHB`.
3. Route handler (`web/src/app/api/market-stats/[symbol]/route.ts`) →
   `backendFetch("/market-stats/USDTTHB")` → `proxyJson`.
4. FastAPI `market_stats` (`api/bases/lf_tool/liqflow_api/core.py`) →
   `repo.get_latest_market_stats("USDTTHB")`.
5. `PostgresOrderbookRepository` → `SELECT * FROM
   liqflow.get_latest_market_stats($1)`.
6. Response bubbles up; `marketStatsSchema.parse` validates before render.

### Sequence diagram — primary/critical business flow (order-book ingest + public read)

```mermaid
sequenceDiagram
    autonumber
    participant P as OrderbookPoller
    participant C as OrderBookClient
    participant B as Binance TH
    participant R as Repository
    participant D as Postgres
    participant BR as Browser
    participant BFF as Next.js BFF
    participant A as FastAPI

    loop every poll_interval_seconds (5s)
        P->>C: get(symbol, limit)
        C->>B: GET /api/v1/depth?symbol=
        B-->>C: {lastUpdateId, bids, asks}
        C-->>P: Orderbook
        P->>R: upsert_orderbook(bids, asks)
        R->>D: SELECT liqflow.upsert_orderbook($1..$4)
    end
    BR->>BFF: GET /api/orderbook/USDTTHB
    BFF->>A: GET /orderbook/USDTTHB
    A->>R: get_latest_orderbook(symbol)
    R->>D: SELECT liqflow.get_latest_orderbook($1)
    D-->>A: row (or none → 404)
    A-->>BFF: TopOfBook (best bid/ask + spread + preview)
    BFF-->>BR: JSON (zod-validated client-side)
```

### Sequence diagram — newly added feature (24hr market stats)

```mermaid
sequenceDiagram
    autonumber
    participant P as OrderbookPoller
    participant C as OrderBookClient
    participant B as Binance TH
    participant R as Repository
    participant D as Postgres
    participant W as MarketStatsWidget
    participant BFF as Next.js BFF
    participant A as FastAPI

    loop every poll_interval_seconds (5s)
        Note over P: after the order-book upsert, in a try/except
        P->>C: get_ticker_24hr(symbol)
        C->>B: GET /api/v1/ticker/24hr?symbol=
        B-->>C: Ticker24hr JSON
        C-->>P: Ticker24hr
        P->>R: upsert_market_stats($1..$8)
        R->>D: SELECT liqflow.upsert_market_stats(...)
        Note over P: on failure → logger.warning, loop continues
    end
    W->>BFF: GET /api/market-stats/USDTTHB (every 3s)
    BFF->>A: GET /market-stats/USDTTHB
    A->>R: get_latest_market_stats(symbol.upper())
    R->>D: SELECT liqflow.get_latest_market_stats($1)
    D-->>A: row (or none)
    alt row present
        A-->>BFF: 200 MarketStatsResponse
    else no snapshot yet
        A-->>BFF: 404 {detail}
    end
    BFF-->>W: JSON → marketStatsSchema.parse → render table
```

---

## 3. Directory Structure (annotated)

```
test-developer-hand-on/
├── api/                                  Python service (Polylith workspace)
│   ├── bases/lf_tool/liqflow_api/        composition root (the "base")
│   │   ├── core.py                       FastAPI app, routes, lifespan, response models
│   │   ├── deps.py                       build/teardown pool, session, repo, poller
│   │   └── config.py                     pydantic-settings (LIQFLOW_API_* env)
│   ├── components/lf_tool/               reusable building blocks
│   │   ├── binance_client/               HTTP client (core.py, types.py) → get_ticker_24hr
│   │   ├── bitkub_client/                NEW: Bitkub public client → get_ticker / get_books
│   │   ├── orderbook_poller/             background asyncio poll loop
│   │   ├── orderbook_repo/               repository: core.py (Protocol), postgres.py, types.py
│   │   └── auth/                         JWT + RBAC dependencies
│   ├── projects/liqflow_api/             deployable: pyproject + Dockerfile + .env.example
│   ├── scripts/play_ticker.py            live ticker + quant metrics (bonus)
│   └── test/                             unit + opt-in integration tests
├── db/                                   golang-migrate up/down pairs
│   ├── 000001..000003_*                  baseline schema, functions, seed
│   └── 000004_market_stats.{up,down}.sql NEW: table + stored functions + trigger
├── web/                                  Next.js 15 (frontend + BFF)
│   └── src/
│       ├── app/                          App Router pages + /api/* route handlers (BFF)
│       │   ├── page.tsx                  public home: MarketStatsWidget + TopOfBook
│       │   ├── (admin)/admin/page.tsx    NEW: tabbed admin (Overview / Exchange Compare)
│       │   ├── api/market-stats/[symbol]/route.ts       BFF proxy
│       │   └── api/admin/exchange-compare/route.ts      NEW admin BFF proxy
│       ├── features/orderbook/           api.ts · hooks.ts · types.ts · components/
│       ├── features/admin/               NEW: exchange-compare schema/hook/ExchangeCompareWidget
│       └── lib/api/backend.ts            single seam to the Python API
├── tools/migration-report/main.go        NEW: golang-migrate before/after report
├── docs/                                  design.md · migration-report.md · these three docs
├── compose.yaml                          postgres → migrate → api → web
└── .forgejo/workflows/ci.yml             CI: api · web · db-integration (NEW job)
```

---

## 4. Component Breakdown

| Component | Inputs | Outputs | Depends on |
| --------- | ------ | ------- | ---------- |
| `OrderBookClient` (`binance_client`) | `symbol`, injected `aiohttp` session | `Orderbook`, `Ticker24hr`; raises `BinanceClientError` | Binance TH REST |
| `BitkubClient` (`bitkub_client`) | injected `aiohttp` session, `sym` | ticker board dict, `BitkubBooks`; raises `BitkubClientError` | Bitkub REST |
| `OrderbookPoller` | client, repo, symbols, interval, limit | side effects (DB upserts), status dict | client, repo, `asyncio` |
| `PostgresOrderbookRepository` | method args | Pydantic models (`OrderbookSnapshot`, `MarketStats`, `User`) | asyncpg pool, stored functions |
| `OrderbookRepository` (Protocol) | — | typing seam | — |
| FastAPI base (`liqflow_api`) | HTTP requests | JSON responses | repo, auth, poller (via `app.state`) |
| BFF route handlers | HTTP requests | proxied JSON | `backendFetch`/`proxyJson` |
| `MarketStatsWidget` / hooks | `symbol` | rendered table | TanStack Query, zod |
| `ExchangeCompareWidget` / hooks | — | 3 comparison tables (5s poll) | TanStack Query, zod |

**Boundary interactions:** the browser crosses only the Next.js boundary; the
Python API is server-only (in Docker it is reachable at `http://api:8000`, never
from the browser). The repo is the only component that speaks SQL, and only via
stored functions.

---

## 5. External Dependencies & Integrations

- **Binance TH public REST** (`https://api.binance.th`) — `GET /api/v1/depth`,
  `GET /api/v1/ticker/24hr`. Unauthenticated. Base URL configurable via
  `LIQFLOW_API_BINANCE_BASE_URL`.
- **Bitkub public REST** (`https://api.bitkub.com`) — `GET /api/market/ticker`
  (whole board; no `sym` filter — returns error 99), `GET /api/market/books`.
  Unauthenticated. Used only by `GET /admin/exchange-compare` (live per request,
  no persistence); base URL is a client-default constant (no env var).
- **Postgres 16** (`postgres:16-alpine`) — schema `liqflow`; access via asyncpg
  pool + stored functions. Migrations applied by golang-migrate.
- **golang-migrate** — `migrate/migrate:v4.18.1` container in `compose.yaml`;
  the `tools/migration-report` Go program links the library driver
  `github.com/golang-migrate/migrate/v4/database/postgres` (pgx `database/sql`
  backend via `github.com/jackc/pgx/v5/stdlib`).
- **No cache / message broker** — there is no Redis, RabbitMQ, or Kafka. State is
  Postgres-only; the "queue" is the in-process poll loop.

> **Assumption:** the web tier's auth/session pieces (middleware, login) exist in
> the baseline. The market-stats change set adds no new external integration; the
> later admin exchange-compare feature adds one (Bitkub public REST), reached only
> via the admin endpoint.

---

## 6. Configuration & Runtime Setup

### Entry points

- **API:** `liqflow-api` console script → `main()` in `core.py` →
  `uvicorn.run(app, host=LIQFLOW_API_HOST, port=LIQFLOW_API_PORT)`. The
  `lifespan` builds deps and **starts the poller**.
- **Web:** Next.js server (`pnpm dev` locally, production build in Docker).
- **Migration report (tooling):** `go run . -path ../../db` with `DSN` env.

### Environment variables (runtime, `LIQFLOW_API_` prefix — `config.py`)

| Var | Default | Purpose |
| --- | ------- | ------- |
| `LIQFLOW_API_POSTGRES_DSN` | `postgresql://liqflow:liqflow@localhost:5432/liqflow` | asyncpg DSN |
| `LIQFLOW_API_BINANCE_BASE_URL` | `https://api.binance.th` | exchange base URL |
| `LIQFLOW_API_POLL_INTERVAL_SECONDS` | `5.0` | poll cadence |
| `LIQFLOW_API_ORDERBOOK_LIMIT` | `20` | depth levels fetched |
| `LIQFLOW_API_HTTP_TOTAL_TIMEOUT_SECONDS` | `10.0` | outbound exchange-call total timeout (bounds hung upstreams) |
| `LIQFLOW_API_HTTP_CONNECT_TIMEOUT_SECONDS` | `5.0` | outbound exchange-call connect timeout |
| `LIQFLOW_API_SYMBOLS` | `["USDTTHB"]` | symbols polled (JSON list) |
| `LIQFLOW_API_JWT_SECRET` | dev default (non-secret) | HS256 signing |
| `LIQFLOW_API_JWT_EXPIRES_MINUTES` | `720` | token TTL |

Web: `BACKEND_API_BASE_URL` (server-side base URL the BFF uses; `http://api:8000`
in Docker). Tooling: `DSN` for the migration report.

### Docker orchestration (`compose.yaml`)

Startup order via healthchecks / `depends_on`:
`postgres` (healthy) → `migrate` (runs `up`, exits 0) → `api` (healthy on
`/health`) → `web`. Host ports are overridable (`POSTGRES_PORT`, `API_PORT`,
`WEB_PORT`). One command: `docker compose up --build`.

> **Local dev note:** a local Postgres often shadows `5432`; run the compose DB
> on `5433` (`POSTGRES_PORT=5433`) for integration tests / the migration report,
> matching `docs/migration-report.md`.

### Background jobs

The only background job is `OrderbookPoller` (in-process `asyncio` task, started
in the API lifespan, stopped in `close_deps`). No cron, no external scheduler.

### CI (`.forgejo/workflows/ci.yml`)

Three jobs: `api` (ruff + pytest), `web` (typecheck + vitest), and the new
`db-integration` (spins Postgres 16, installs the golang-migrate CLI, applies
migrations, runs the **before/after report** Go program, then runs the
DB-backed pytest suite with `LIQFLOW_API_TEST_DSN`).

---

## 7. Scalability & Extension Guide

### Bottlenecks (inferred)

- **In-process poller** — the primary scaling limit: two API replicas both poll
  and race on the same upsert. To scale out, extract the poller into its own
  worker (single replica, or leader-elected), and let API replicas be
  read-only. (This is the code's own "candidate question".)
- **Latest-only tables** — reads are O(1) and cheap; the constraint is *history*,
  not throughput. Analytics need an append-only design.
- **Connection pool** — sized by `pg_min_connections`/`pg_max_connections`
  (1–10); tune with replica count.

### Extending the feature

- **Add a symbol:** append to `LIQFLOW_API_SYMBOLS`. The poller, upsert, endpoint
  (`/market-stats/{symbol}`), and widget already parametrise on `symbol` — no
  code change. (The `config.py` comment notes only `USDTTHB` is used today.)
- **Add a field from the ticker:** add the column (new migration), extend
  `upsert_market_stats`/`get_latest_market_stats`, `MarketStats`,
  `MarketStatsResponse`, `marketStatsSchema`, and the widget. The `TypedDict`
  already carries the raw field.
- **Add history:** new append-only table `market_stats_history(symbol, ts, ...)`
  with an index on `(symbol, ts DESC)`; write from the same poll branch; add a
  time-range read function.
- **Harden the feed:** promote the silent ticker warning into a metric/alert;
  add runtime validation of the raw ticker payload.

### Horizontal vs vertical

- **Vertical:** raise pool size + poll interval budget for more symbols on one
  box — fine to a point.
- **Horizontal:** stateless API + BFF scale trivially behind a load balancer;
  the poller must be singled-out first (above) to avoid duplicate polling.
