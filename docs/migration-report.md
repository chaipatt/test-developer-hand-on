# Before/after migration report

Task item: *"Show a before/after migration report using
`github.com/golang-migrate/migrate/v4/database/postgres`."*

`tools/migration-report/` is a small Go program that opens the DB through the
**official golang-migrate Postgres driver**
(`github.com/golang-migrate/migrate/v4/database/postgres`, pgx `database/sql`
backend), reads the current schema version, rolls the newest migration back one
step, then re-applies it — printing the version at each hop. This exercises the
new `000004_market_stats` migration in **both directions** (down then up).

## Run

```bash
# DB up on 5433 (local pg shadows 5432):  POSTGRES_PORT=5433 docker compose up -d postgres migrate
cd tools/migration-report
DSN='postgres://liqflow:liqflow@localhost:5433/liqflow?sslmode=disable&search_path=public' \
  go run . -path ../../db
```

## Output

```
=== golang-migrate before/after report ===
driver:  github.com/golang-migrate/migrate/v4/database/postgres
source:  file://../../db

BEFORE (current):  version 4 (dirty=false)
after down 1:      version 3 (dirty=false)
AFTER up 1:        version 4 (dirty=false)

OK: newest migration verified in both directions (down then up).
```

Reading it:

- **BEFORE = 4** — `000004_market_stats.up.sql` is applied (table + stored
  functions + trigger present).
- **after down 1 = 3** — `000004_market_stats.down.sql` cleanly dropped the
  functions and table; schema is back at the baseline (`000003`).
- **AFTER up 1 = 4** — re-applied without error, `dirty=false` throughout (no
  half-applied/failed state). A dirty flag here would mean a migration crashed
  mid-way and needs manual `force`.

The plain CLI equivalent (`migrate ... version` / `down 1` / `up 1`) uses the
same driver; the Go program just makes the before/after transition explicit and
self-checking for CI.
