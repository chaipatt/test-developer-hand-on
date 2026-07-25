"""Repo integration test against a real Postgres (opt-in).

Set LIQFLOW_API_TEST_DSN to a database that has the migrations applied, e.g.:

    LIQFLOW_API_TEST_DSN=postgresql://liqflow:liqflow@localhost:5432/liqflow \\
        uv run pytest test/orderbook_repo

Skipped when the env var is absent so the default `uv run pytest` stays offline.
"""

import os

import pytest
import pytest_asyncio
from lf_tool.orderbook_repo import PostgresOrderbookRepository, create_pool

DSN = os.environ.get("LIQFLOW_API_TEST_DSN")

pytestmark = pytest.mark.skipif(
    not DSN, reason="set LIQFLOW_API_TEST_DSN to run repo integration tests"
)


@pytest_asyncio.fixture()
async def repo():
    pool = await create_pool(DSN)
    try:
        yield PostgresOrderbookRepository(pool)
    finally:
        await pool.close()


@pytest.mark.asyncio
async def test_upsert_then_get_latest_roundtrips(repo):
    bids = [["34.10", "5.0"], ["34.05", "2.0"]]
    asks = [["34.20", "1.0"]]
    stored = await repo.upsert_orderbook("TESTPAIR", 99, bids, asks)
    assert stored.symbol == "TESTPAIR"

    latest = await repo.get_latest_orderbook("TESTPAIR")
    assert latest is not None
    assert latest.last_update_id == 99
    assert latest.bids == bids
    assert latest.asks == asks


@pytest.mark.asyncio
async def test_seeded_users_present(repo):
    admin = await repo.get_user_by_email("admin@liqflow.test")
    assert admin is not None
    assert admin.role == "admin"
    assert admin.is_active is True

    unauthorized = await repo.get_user_by_email("unauthorized@liqflow.test")
    assert unauthorized is not None
    assert unauthorized.is_active is False


@pytest.mark.asyncio
async def test_market_stats_upsert_and_get(repo):
    stored = await repo.upsert_market_stats(
        symbol="TESTPAIR",
        price_change="0.50",
        price_change_pct="1.50",
        last_price="34.50",
        high_price="35.00",
        low_price="34.00",
        volume="5000.0",
        quote_volume="172500.0",
    )
    assert stored.symbol == "TESTPAIR"

    latest = await repo.get_latest_market_stats("TESTPAIR")
    assert latest is not None
    assert latest.last_price == "34.50"
    assert latest.high_price == "35.00"

