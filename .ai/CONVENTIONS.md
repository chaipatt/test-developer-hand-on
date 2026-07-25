# Conventions

Keep changes consistent with the surrounding code. Highlights:

## Python (`api/` — the `liqflow_api` service)
- Lives in `api/` as a Polylith workspace; run `uv`/`poly` commands from there.
- **Polylith, loose theme**, namespace `lf_tool`. Components expose behaviour
  through `core.py` (interfaces / pure logic); infrastructure lives in sibling
  modules (e.g. `postgres.py`). Bases wire components together.
- **DB access only through stored functions.** The repo builds a positional
  param tuple, calls `SELECT * FROM liqflow.fn($1, …)`, and maps rows to
  pydantic models. No inline DML in Python.
- **Config** via pydantic-settings, env prefix `LIQFLOW_API_`.
- **Logging** is plain stdlib `logging` (minimal by design — not a focus).
- **Tests**: `uv run pytest`. Unit tests use fakes (no DB/network); the repo
  integration test is opt-in via `LIQFLOW_API_TEST_DSN`.
- Lint/format: `uv run ruff check .` / `uv run ruff format .`.

## TypeScript (`web`)
- **Feature-sliced**: `src/features/<f>/{api.ts,types.ts,hooks.ts,components/}`.
  `api.ts` calls the BFF (`/api/*`), `types.ts` holds zod schemas, `hooks.ts`
  wraps TanStack Query. Pages are thin client shells.
- **The frontend never calls the Python API directly** — always through a BFF
  route in `src/app/api/**` and the `src/lib/api/backend.ts` wrapper.
- **The UI is a wireframe, not a design task**: plain, colorless, structural
  (bare tables + minimal Tailwind). Don't invest in visual polish.
- **Tests**: `pnpm test` (vitest). Colocate `route.test.ts` next to handlers.

## SQL (`db`)
- golang-migrate pairs `NNNNNN_<name>.{up,down}.sql`. UPPERCASE keywords,
  snake_case identifiers, named constraints, `idx_` index prefix, `COMMENT ON`
  every table + non-obvious column. Down migrations reverse in dependency order.
