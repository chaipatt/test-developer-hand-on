# developer-hand-on-test

A small, self-contained hands-on test repo that mirrors Liqflow's real
architecture in one vertical slice:

> **Binance TH order book → API → Postgres → API → BFF → frontend**, with a
> public view, one login, and RBAC (unauthorized / user / admin).

The runnable baseline here is the fixture. Your role tasks are in
[`TASKS.md`](TASKS.md). Read [`.ai/ARCHITECTURE.md`](.ai/ARCHITECTURE.md) first.

- **Python API** — FastAPI, Polylith (`liqflow_api`), asyncpg + stored functions.
- **Web** — Next.js 15 (App Router, React 19) frontend **and** BFF.
- **DB** — Postgres, golang-migrate migrations + seed.
- **Run** — one command with `docker compose`.

---

## Quick start (one command)

Requires Docker + Docker Compose.

```bash
docker compose up --build
```

That brings up, in order: **Postgres → migrate (applies `db/`) → API → web**.
When it's ready:

- Web UI: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- API health: <http://localhost:8000/health>

Stop with `Ctrl-C`; `docker compose down -v` also removes the database volume.

### Demo accounts

All three share one **local-only, non-secret** password: `LiqflowDemo!23`.

| Email                       | Role  | What it demonstrates                                        |
| --------------------------- | ----- | ---------------------------------------------------------- |
| `unauthorized@liqflow.test` | —     | Disabled account → login is rejected (unauthorized path).  |
| `user@liqflow.test`         | user  | Sees the public book + full depth (`/dashboard`).          |
| `admin@liqflow.test`        | admin | Everything a user sees + admin views (`/admin`).           |

Try: open `/` (public, no login) → sign in as `user@` → `/dashboard` works,
`/admin` redirects to `/permission-denied` → sign in as `admin@` → `/admin`
shows the user list + poller status.

---

## What to click

| Route               | Access | Shows                                             |
| ------------------- | ------ | ------------------------------------------------- |
| `/`                 | public | Top-of-book for `USDTTHB` (best bid/ask + spread) |
| `/login`            | public | Sign-in form (seeded users)                       |
| `/dashboard`        | user   | Full order-book depth                             |
| `/admin`            | admin  | Poller status + user list + full depth            |
| `/permission-denied`| public | Shown when a role check fails                      |

---

## Local development (without Docker)

### 1. Postgres + migrations

Run Postgres however you like (or just `docker compose up postgres migrate`).
To apply migrations manually with golang-migrate:

```bash
# search_path=public keeps migrate's schema_migrations table out of the
# liqflow schema (the DB user is also named "liqflow").
DSN='postgres://liqflow:liqflow@localhost:5432/liqflow?sslmode=disable&search_path=public'
migrate -path db -database "$DSN" up
```

`migrate` also prints a **before/after** view — check the applied version:

```bash
migrate -path db -database "$DSN" version    # current schema version (before/after)
migrate -path db -database "$DSN" down 1     # roll back one step
```

### 2. Python API

The Python service is a Polylith workspace under `api/`:

```bash
cd api
uv run pytest                 # unit tests (no DB/network needed)
LIQFLOW_API_POSTGRES_DSN='postgresql://liqflow:liqflow@localhost:5432/liqflow' \
  uv run liqflow-api          # serves on http://localhost:8000
```

Opt-in repo integration tests (need a migrated DB):

```bash
cd api
LIQFLOW_API_TEST_DSN='postgresql://liqflow:liqflow@localhost:5432/liqflow' \
  uv run pytest test/orderbook_repo
```

### 3. Web

```bash
cd web
pnpm install
BACKEND_API_BASE_URL='http://localhost:8000' pnpm dev   # http://localhost:3000
pnpm test        # vitest (BFF route tests)
pnpm typecheck
```

---

## Layout

```
api/                              the Python service (Polylith workspace)
  bases/lf_tool/liqflow_api/      FastAPI app + config + deps (the Polylith base)
  components/lf_tool/             binance_client · orderbook_poller · orderbook_repo · auth
  projects/liqflow_api/           deployable: pyproject + Dockerfile + .env.example
  workspace.toml, pyproject.toml, uv.lock, mise.toml, ruff/pytest/mypy config
db/                               golang-migrate up/down pairs (schema, functions, seed)
web/                              Next.js 15 app (frontend + BFF)
compose.yaml                      postgres + migrate + api + web
.ai/                              ARCHITECTURE / CONVENTIONS / SECURITY (read these)
TASKS.md                          your role tasks + questions
```

## Backend task additions

Added the Binance TH **24hr ticker** feed end to end (client → poller → DB →
API → BFF → frontend), plus supporting tooling. See [`docs/design.md`](docs/design.md)
for UML (component / sequence / ER).

| What | Where |
| ---- | ----- |
| New Binance client method `get_ticker_24hr` | `api/components/lf_tool/binance_client/` |
| Migration `000004_market_stats` (table + stored functions) | `db/000004_market_stats.{up,down}.sql` |
| Public endpoint `GET /market-stats/{symbol}` + BFF proxy | `api/bases/.../liqflow_api/core.py`, `web/src/app/api/market-stats/` |
| Frontend `MarketStatsWidget` | `web/src/features/orderbook/components/market-stats.tsx` |
| Before/after migration report (golang-migrate/postgres driver) | `tools/migration-report/`, [`docs/migration-report.md`](docs/migration-report.md) |
| Cross-exchange CLI board (Binance TH vs Bitkub) | `api/scripts/play_ticker.py` |
| CI job: migrate + integration tests + migration report | `.forgejo/workflows/ci.yml` (`db-integration`) |

```bash
# migration before/after report (needs DB on 5433)
cd tools/migration-report && DSN='postgres://liqflow:liqflow@localhost:5433/liqflow?sslmode=disable&search_path=public' go run . -path ../../db

# live Binance TH vs Bitkub comparison board (from root or api/)
uv run --project api python api/scripts/play_ticker.py
# or: cd api && uv run python scripts/play_ticker.py
```

Also fixed a latent bug in the baseline poller: bids/asks were swapped when
persisting snapshots (`orderbook_poller/core.py`).

## Admin feature: cross-exchange comparison (Binance TH vs Bitkub)

An **admin-only** live comparison of Binance TH and Bitkub for the THB pairs
`USDTTHB`, `BTCTHB`, `ETHTHB`. Each request fetches the 24hr ticker + order-book
depth from **both** exchanges concurrently and returns, per pair: last price,
24h change %, quote volume, best bid/ask, spread %, and the **arbitrage spread %**
(Bitkub last vs Binance last). All money math uses `Decimal` (no float rounding);
each exchange fetch is isolated so one side failing degrades to an `error` row,
never a 500.

| What | Where |
| ---- | ----- |
| New Bitkub public client (`get_ticker`, `get_books`, `to_bitkub_symbol`) | `api/components/lf_tool/bitkub_client/` |
| Admin endpoint `GET /admin/exchange-compare` (`Depends(require_admin)`) | `api/bases/.../liqflow_api/core.py` |
| BFF proxy (session token → backend) | `web/src/app/api/admin/exchange-compare/route.ts` |
| Frontend `ExchangeCompareWidget` (3 tables, polls every 5s) + admin tabs | `web/src/features/admin/components/exchange-compare.tsx`, `web/src/app/(admin)/admin/page.tsx` |

Notes: the endpoint calls both exchanges live per request (polled every 5s from
the UI) — no persistence, no migration, no new required env vars. Bitkub's ticker
no longer accepts a `sym` filter (returns error 99), so the client fetches the
whole board and indexes by `THB_<base>`; the ticker's `highestBid`/`lowestAsk`
are treated as the authoritative top-of-book (the `/books` outer rows can be
stale), with the book rate as fallback.

```bash
# same cross-exchange comparison, as a standalone CLI board:
uv run --project api python api/scripts/play_ticker.py
```

## License

[Business Source License 1.1](LICENSE) (Licensor: Liqflow). Non-production /
evaluation use is granted; each version converts to Apache-2.0 four years after
its release. See the LICENSE file for the exact parameters.
