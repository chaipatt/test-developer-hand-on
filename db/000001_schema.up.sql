-- 000001_schema (up): base schema for the liqflow hands-on test.
-- Conventions (mirrors our production migration style): UPPERCASE keywords,
-- snake_case identifiers, named constraints, `idx_` index prefix, and a
-- COMMENT ON for every table and non-obvious column. golang-migrate wraps each
-- migration in a transaction, so no explicit BEGIN/COMMIT here.

CREATE SCHEMA IF NOT EXISTS liqflow;

COMMENT ON SCHEMA liqflow IS
    'Application schema for the developer hands-on test (users + order-book snapshots).';

-- ---------------------------------------------------------------------------
-- Shared trigger function: stamp updated_at on every UPDATE.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION liqflow.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = liqflow, public
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION liqflow.set_updated_at() IS
    'Trigger function: sets updated_at to the current timestamp on every UPDATE.';

-- ---------------------------------------------------------------------------
-- users: seeded accounts that drive the login + RBAC demo.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS liqflow.users (
    id            BIGSERIAL   PRIMARY KEY,
    email         TEXT        NOT NULL,
    password_hash TEXT        NOT NULL,
    role          TEXT        NOT NULL,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    description   TEXT        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_role CHECK (role IN ('user', 'admin'))
);

COMMENT ON TABLE liqflow.users IS
    'Seeded demo accounts. Each row documents (via description) what auth/RBAC path it demonstrates.';
COMMENT ON COLUMN liqflow.users.email IS 'Login identifier (unique).';
COMMENT ON COLUMN liqflow.users.password_hash IS 'bcrypt hash of the shared local-only demo password.';
COMMENT ON COLUMN liqflow.users.role IS 'RBAC role: ''user'' or ''admin''.';
COMMENT ON COLUMN liqflow.users.is_active IS 'When FALSE, login is rejected (the unauthorized path).';
COMMENT ON COLUMN liqflow.users.description IS 'Human note explaining what this seeded account demonstrates.';

CREATE OR REPLACE TRIGGER trg_users_set_updated_at
    BEFORE UPDATE ON liqflow.users
    FOR EACH ROW
    EXECUTE FUNCTION liqflow.set_updated_at();

-- ---------------------------------------------------------------------------
-- orderbook_snapshots: latest polled order book per symbol (upsert-in-place).
-- One row per symbol; the poller overwrites it each interval. Keeping only the
-- latest row is a deliberate simplification and a candidate optimization hook
-- (e.g. keep history / partition by time / stream deltas).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS liqflow.orderbook_snapshots (
    id             BIGSERIAL   PRIMARY KEY,
    symbol         TEXT        NOT NULL,
    last_update_id BIGINT,
    bids           JSONB       NOT NULL,
    asks           JSONB       NOT NULL,
    ts             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_orderbook_snapshots_symbol UNIQUE (symbol)
);

COMMENT ON TABLE liqflow.orderbook_snapshots IS
    'Latest order-book snapshot per symbol, upserted by the poller from the Binance TH depth API.';
COMMENT ON COLUMN liqflow.orderbook_snapshots.symbol IS 'Exchange symbol, e.g. USDTTHB.';
COMMENT ON COLUMN liqflow.orderbook_snapshots.last_update_id IS 'Binance lastUpdateId of this snapshot.';
COMMENT ON COLUMN liqflow.orderbook_snapshots.bids IS 'Array of [price, quantity] string pairs (bids), highest price first.';
COMMENT ON COLUMN liqflow.orderbook_snapshots.asks IS 'Array of [price, quantity] string pairs (asks), lowest price first.';
COMMENT ON COLUMN liqflow.orderbook_snapshots.ts IS 'When this snapshot was captured by the poller.';

CREATE INDEX IF NOT EXISTS idx_orderbook_snapshots_ts
    ON liqflow.orderbook_snapshots (ts DESC);

CREATE OR REPLACE TRIGGER trg_orderbook_snapshots_set_updated_at
    BEFORE UPDATE ON liqflow.orderbook_snapshots
    FOR EACH ROW
    EXECUTE FUNCTION liqflow.set_updated_at();
