-- 000002_functions (up): stored functions are the only DB access path the API
-- uses (our production house rule: the repo layer never runs inline DML).

-- ---------------------------------------------------------------------------
-- upsert_orderbook: overwrite the latest snapshot for a symbol.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION liqflow.upsert_orderbook(
    i_symbol         TEXT,
    i_last_update_id BIGINT,
    i_bids           JSONB,
    i_asks           JSONB
)
RETURNS SETOF liqflow.orderbook_snapshots
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = liqflow, public
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO liqflow.orderbook_snapshots (symbol, last_update_id, bids, asks, ts)
    VALUES (i_symbol, i_last_update_id, i_bids, i_asks, now())
    ON CONFLICT (symbol) DO UPDATE
        SET last_update_id = EXCLUDED.last_update_id,
            bids           = EXCLUDED.bids,
            asks           = EXCLUDED.asks,
            ts             = now()
    RETURNING *;
END;
$$;

COMMENT ON FUNCTION liqflow.upsert_orderbook(TEXT, BIGINT, JSONB, JSONB) IS
    'Insert or overwrite the latest order-book snapshot for a symbol; returns the stored row.';

-- ---------------------------------------------------------------------------
-- get_latest_orderbook: read the latest snapshot for a symbol.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION liqflow.get_latest_orderbook(i_symbol TEXT)
RETURNS SETOF liqflow.orderbook_snapshots
LANGUAGE sql
SECURITY INVOKER
SET search_path = liqflow, public
STABLE PARALLEL SAFE
AS $$
    SELECT *
    FROM liqflow.orderbook_snapshots
    WHERE symbol = i_symbol;
$$;

COMMENT ON FUNCTION liqflow.get_latest_orderbook(TEXT) IS
    'Return the latest stored order-book snapshot for a symbol (0 or 1 row).';

-- ---------------------------------------------------------------------------
-- get_user_by_email: used by the auth flow to verify a login.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION liqflow.get_user_by_email(i_email TEXT)
RETURNS SETOF liqflow.users
LANGUAGE sql
SECURITY INVOKER
SET search_path = liqflow, public
STABLE PARALLEL SAFE
AS $$
    SELECT *
    FROM liqflow.users
    WHERE email = i_email;
$$;

COMMENT ON FUNCTION liqflow.get_user_by_email(TEXT) IS
    'Return the user row for a given email (0 or 1 row).';

-- ---------------------------------------------------------------------------
-- list_users: admin-only view of all seeded accounts.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION liqflow.list_users()
RETURNS SETOF liqflow.users
LANGUAGE sql
SECURITY INVOKER
SET search_path = liqflow, public
STABLE PARALLEL SAFE
AS $$
    SELECT *
    FROM liqflow.users
    ORDER BY id;
$$;

COMMENT ON FUNCTION liqflow.list_users() IS
    'Return all users ordered by id (admin view).';
