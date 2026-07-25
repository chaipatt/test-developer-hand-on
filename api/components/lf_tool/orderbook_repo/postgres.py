"""Postgres implementation of :class:`OrderbookRepository`.

All access goes through stored functions (our production house rule: the repo
never runs inline DML). A jsonb binary codec is registered per-connection
so ``bids``/``asks`` round-trip as native Python lists.
"""

from __future__ import annotations

from typing import List, Optional

import asyncpg
import orjson
from lf_tool.orderbook_repo.types import MarketStats, OrderbookSnapshot, User

_UPSERT_ORDERBOOK_SQL = "SELECT * FROM liqflow.upsert_orderbook($1, $2, $3, $4);"
_GET_LATEST_ORDERBOOK_SQL = "SELECT * FROM liqflow.get_latest_orderbook($1);"
_UPSERT_MARKET_STATS_SQL = "SELECT * FROM liqflow.upsert_market_stats($1, $2, $3, $4, $5, $6, $7, $8);"
_GET_LATEST_MARKET_STATS_SQL = "SELECT * FROM liqflow.get_latest_market_stats($1);"
_GET_USER_BY_EMAIL_SQL = "SELECT * FROM liqflow.get_user_by_email($1);"
_LIST_USERS_SQL = "SELECT * FROM liqflow.list_users();"


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Encode/decode jsonb via orjson (house standard binary codec)."""
    await conn.set_type_codec(
        "jsonb",
        schema="pg_catalog",
        encoder=lambda v: b"\x01" + orjson.dumps(v),
        decoder=lambda b: orjson.loads(b[1:]),
        format="binary",
    )


async def create_pool(
    dsn: str, min_connections: int = 1, max_connections: int = 10
) -> asyncpg.Pool:
    """Create an asyncpg pool with the jsonb codec installed."""
    if not dsn:
        raise ValueError("PostgreSQL DSN is required")
    return await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_connections,
        max_size=max_connections,
        init=_init_connection,
    )


class PostgresOrderbookRepository:
    """Order-book + user repository backed by Postgres stored functions."""

    def __init__(self, pool: asyncpg.Pool, acquire_timeout: float = 10.0) -> None:
        self._pool = pool
        self._acquire_timeout = acquire_timeout

    async def upsert_orderbook(
        self,
        symbol: str,
        last_update_id: Optional[int],
        bids: List[List[str]],
        asks: List[List[str]],
    ) -> OrderbookSnapshot:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            row = await conn.fetchrow(
                _UPSERT_ORDERBOOK_SQL, symbol, last_update_id, bids, asks
            )
        return OrderbookSnapshot(**dict(row))

    async def get_latest_orderbook(self, symbol: str) -> Optional[OrderbookSnapshot]:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            row = await conn.fetchrow(_GET_LATEST_ORDERBOOK_SQL, symbol)
        return OrderbookSnapshot(**dict(row)) if row else None

    async def upsert_market_stats(
        self,
        symbol: str,
        price_change: str,
        price_change_pct: str,
        last_price: str,
        high_price: str,
        low_price: str,
        volume: str,
        quote_volume: str,
    ) -> MarketStats:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            row = await conn.fetchrow(
                _UPSERT_MARKET_STATS_SQL,
                symbol,
                price_change,
                price_change_pct,
                last_price,
                high_price,
                low_price,
                volume,
                quote_volume,
            )
        return MarketStats(**dict(row))

    async def get_latest_market_stats(self, symbol: str) -> Optional[MarketStats]:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            row = await conn.fetchrow(_GET_LATEST_MARKET_STATS_SQL, symbol)
        return MarketStats(**dict(row)) if row else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            row = await conn.fetchrow(_GET_USER_BY_EMAIL_SQL, email)
        return User(**dict(row)) if row else None

    async def list_users(self) -> List[User]:
        async with self._pool.acquire(timeout=self._acquire_timeout) as conn:
            rows = await conn.fetch(_LIST_USERS_SQL)
        return [User(**dict(row)) for row in rows]

