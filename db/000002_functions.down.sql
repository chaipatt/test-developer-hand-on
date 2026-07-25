-- 000002_functions (down): drop the stored functions.

DROP FUNCTION IF EXISTS liqflow.list_users();
DROP FUNCTION IF EXISTS liqflow.get_user_by_email(TEXT);
DROP FUNCTION IF EXISTS liqflow.get_latest_orderbook(TEXT);
DROP FUNCTION IF EXISTS liqflow.upsert_orderbook(TEXT, BIGINT, JSONB, JSONB);
