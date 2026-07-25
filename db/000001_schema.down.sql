-- 000001_schema (down): reverse of the up migration, in dependency order.

DROP TABLE IF EXISTS liqflow.orderbook_snapshots CASCADE;
DROP TABLE IF EXISTS liqflow.users CASCADE;
DROP FUNCTION IF EXISTS liqflow.set_updated_at();
DROP SCHEMA IF EXISTS liqflow;
