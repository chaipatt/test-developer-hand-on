# Architecture

A single vertical slice that mirrors Liqflow's real stack, simplified:

```
Binance TH /api/v1/depth ──poll──▶ liqflow_api (FastAPI, Polylith)
                                      │  orderbook_poller (lifespan task)
                                      │  orderbook_repo ──▶ Postgres (stored fns)
                                      │  auth (bcrypt + JWT, RBAC)
                                      ▼
                         Next.js BFF (src/app/api/*) ──▶ draft-frame frontend
                              (public / login / user / admin)
```

## Components

### `api/` — Python service `liqflow_api` (Polylith, namespace `lf_tool`)
- **`binance_client`** — tiny public client for `GET /api/v1/depth` and
  `GET /api/v1/ticker/24hr` (attrs + aiohttp; the session is injected, not owned).
- **`bitkub_client`** — public client for Bitkub `GET /api/market/ticker` +
  `GET /api/market/books` (same attrs shape). Used by the admin cross-exchange
  comparison endpoint; live per request, no persistence.
- **`orderbook_poller`** — async loop started inside the FastAPI `lifespan` as a
  background task. It polls each configured symbol and upserts snapshots.
  *(Deliberate simplification: the poller runs in the API replica. "How would
  you scale this out?" is a built-in candidate question.)*
- **`orderbook_repo`** — Postgres repository. A `Protocol` in `core.py`, a
  `Pg…` implementation in `postgres.py`, pydantic models in `types.py`. Every
  call goes through a **stored function** (never inline DML).
- **`auth`** — verify a seeded user (bcrypt), issue a JWT, resolve
  role/permissions; `require_user` / `require_admin` FastAPI deps.

The base (`api/bases/lf_tool/liqflow_api`) wires it together: `config.py`
(pydantic-settings, env prefix `LIQFLOW_API_`), `deps.py` (build/teardown the
pool + session + poller), `core.py` (the FastAPI app + routes).

**Endpoints**
- `GET /health`, `GET /ready`
- `POST /auth/login` → JWT; `GET /auth/me` → `{email, role, description,
  permissions[]}` (the RBAC endpoint the BFF/UI render from)
- `GET /orderbook/{symbol}` + `GET /market-stats/{symbol}` (public) ·
  `GET /orderbook/{symbol}/full` (user) ·
  `GET /admin/users` + `GET /admin/poller-status` +
  `GET /admin/exchange-compare` (admin — live Binance TH vs Bitkub)

Server-side role checks are authoritative; UI gating is cosmetic on top.

### `web/` — Next.js 15 (App Router, React 19, TS)
- **`src/middleware.ts`** — staged RBAC gate: public allowlist → no session →
  `/login` → `PROTECTED_ROUTES` role check → `/permission-denied`. `deny()`
  returns JSON for `/api/*` and a redirect for pages. Role comes from
  `GET /auth/me`.
- **BFF** — `src/app/api/**/route.ts` proxy every backend call through one
  wrapper (`src/lib/api/backend.ts`, `BACKEND_API_BASE_URL`). The frontend
  never calls the Python API directly.
- **Feature slices** — `src/features/<f>/{api.ts,types.ts,hooks.ts,components/}`
  (`orderbook`, `auth`, `admin`). Pages under `src/app/**` are thin shells.
- **Auth** — email+password against the seeded Postgres users; the BFF stores
  the JWT in an httpOnly cookie (`lf_session`). No external identity provider,
  so the whole thing runs offline under `docker compose`.

> The real Liqflow stack uses Supabase for auth and signs service-to-service
> calls with HMAC. This repo drops both for a self-contained, offline-runnable
> equivalent — a deliberate simplification and a fair critique target.

### `db/` — golang-migrate
`NNNNNN_<name>.{up,down}.sql`, schema `liqflow`: `users` and
`orderbook_snapshots`, a `set_updated_at()` trigger, stored functions, named
constraints/indexes, and `COMMENT ON` on every table + non-obvious column. The
seed migration inserts three demo users, each with a `description`.

### `compose.yaml`
`postgres → migrate → api → web`, one command. The only orchestration in the
repo (k8s is intentionally out of scope for this test).
