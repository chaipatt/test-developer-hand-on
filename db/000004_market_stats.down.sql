-- 000004_market_stats (down): drop stored functions and market_stats table.

DROP FUNCTION IF EXISTS liqflow.get_latest_market_stats(TEXT);
DROP FUNCTION IF EXISTS liqflow.upsert_market_stats(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, TEXT);
DROP TABLE IF EXISTS liqflow.market_stats;
