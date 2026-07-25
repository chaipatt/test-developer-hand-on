"""Dependency wiring: build/teardown the pool, HTTP session, repo and poller.

This is the analogue of a FastAPI lifespan's resource block — everything the
app needs is constructed here and injected onto ``app.state`` by ``core.py``.
"""

from __future__ import annotations

import aiohttp
import asyncpg
from attrs import define
from lf_tool.binance_client import create_client
from lf_tool.liqflow_api.config import LiqflowApiConfig
from lf_tool.orderbook_poller import OrderbookPoller
from lf_tool.orderbook_repo import (
    PostgresOrderbookRepository,
    create_pool,
)


@define(slots=True)
class AppDeps:
    """Live resources shared across requests."""

    pool: asyncpg.Pool
    session: aiohttp.ClientSession
    repo: PostgresOrderbookRepository
    poller: OrderbookPoller


async def build_deps(config: LiqflowApiConfig) -> AppDeps:
    """Construct the pool, HTTP session, repo and poller."""
    pool = await create_pool(
        config.postgres_dsn,
        min_connections=config.pg_min_connections,
        max_connections=config.pg_max_connections,
    )
    timeout = aiohttp.ClientTimeout(
        total=config.http_total_timeout_seconds,
        connect=config.http_connect_timeout_seconds,
    )
    session = aiohttp.ClientSession(timeout=timeout)
    repo = PostgresOrderbookRepository(pool)
    client = create_client(session, base_url=config.binance_base_url)
    poller = OrderbookPoller(
        client=client,
        repo=repo,
        symbols=config.symbols,
        interval_seconds=config.poll_interval_seconds,
        limit=config.orderbook_limit,
    )
    return AppDeps(pool=pool, session=session, repo=repo, poller=poller)


async def close_deps(deps: AppDeps) -> None:
    """Stop the poller and close the session + pool."""
    await deps.poller.stop()
    await deps.session.close()
    await deps.pool.close()
