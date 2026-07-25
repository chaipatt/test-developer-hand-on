-- 000004_market_stats (up): create market_stats table and stored functions.

CREATE TABLE IF NOT EXISTS liqflow.market_stats (
    symbol              TEXT        PRIMARY KEY,
    price_change        TEXT        NOT NULL,
    price_change_pct    TEXT        NOT NULL,
    last_price          TEXT        NOT NULL,
    high_price          TEXT        NOT NULL,
    low_price           TEXT        NOT NULL,
    volume              TEXT        NOT NULL,
    quote_volume        TEXT        NOT NULL,
    ts                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE liqflow.market_stats IS
    '24hr ticker market statistics per symbol polled from Binance TH.';
COMMENT ON COLUMN liqflow.market_stats.symbol IS 'Exchange symbol, e.g. USDTTHB.';
COMMENT ON COLUMN liqflow.market_stats.price_change IS '24hr price change string.';
COMMENT ON COLUMN liqflow.market_stats.price_change_pct IS '24hr price change percentage string.';
COMMENT ON COLUMN liqflow.market_stats.last_price IS 'Last traded price.';
COMMENT ON COLUMN liqflow.market_stats.high_price IS '24hr high price.';
COMMENT ON COLUMN liqflow.market_stats.low_price IS '24hr low price.';
COMMENT ON COLUMN liqflow.market_stats.volume IS '24hr base asset volume.';
COMMENT ON COLUMN liqflow.market_stats.quote_volume IS '24hr quote asset volume.';
COMMENT ON COLUMN liqflow.market_stats.ts IS 'Timestamp when this stat was polled.';

CREATE OR REPLACE TRIGGER trg_market_stats_set_updated_at
    BEFORE UPDATE ON liqflow.market_stats
    FOR EACH ROW
    EXECUTE FUNCTION liqflow.set_updated_at();

-- Stored Function: upsert_market_stats
CREATE OR REPLACE FUNCTION liqflow.upsert_market_stats(
    i_symbol           TEXT,
    i_price_change     TEXT,
    i_price_change_pct TEXT,
    i_last_price       TEXT,
    i_high_price       TEXT,
    i_low_price        TEXT,
    i_volume           TEXT,
    i_quote_volume     TEXT
)
RETURNS SETOF liqflow.market_stats
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = liqflow, public
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO liqflow.market_stats (
        symbol, price_change, price_change_pct, last_price, high_price, low_price, volume, quote_volume, ts
    )
    VALUES (
        i_symbol, i_price_change, i_price_change_pct, i_last_price, i_high_price, i_low_price, i_volume, i_quote_volume, now()
    )
    ON CONFLICT (symbol) DO UPDATE
        SET price_change     = EXCLUDED.price_change,
            price_change_pct = EXCLUDED.price_change_pct,
            last_price       = EXCLUDED.last_price,
            high_price       = EXCLUDED.high_price,
            low_price        = EXCLUDED.low_price,
            volume           = EXCLUDED.volume,
            quote_volume     = EXCLUDED.quote_volume,
            ts               = now()
    RETURNING *;
END;
$$;

COMMENT ON FUNCTION liqflow.upsert_market_stats(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT) IS
    'Insert or overwrite the latest 24hr market stats for a symbol; returns the stored row.';

-- Stored Function: get_latest_market_stats
CREATE OR REPLACE FUNCTION liqflow.get_latest_market_stats(i_symbol TEXT)
RETURNS SETOF liqflow.market_stats
LANGUAGE sql
SECURITY INVOKER
SET search_path = liqflow, public
STABLE PARALLEL SAFE
AS $$
    SELECT *
    FROM liqflow.market_stats
    WHERE symbol = i_symbol;
$$;

COMMENT ON FUNCTION liqflow.get_latest_market_stats(TEXT) IS
    'Return the latest stored market stats for a symbol (0 or 1 row).';
