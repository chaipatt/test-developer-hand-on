"""Background poll loop: Binance TH depth -> repo upsert.

Runs *inside* the FastAPI service as a lifespan background task (a deliberate
simplification — "why is the poller in the API replica, and how would you
scale it out?" is a built-in candidate question). Exposes a status snapshot
for the admin ``/admin/poller-status`` endpoint.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from lf_tool.binance_client import OrderBookClient
from lf_tool.orderbook_repo import OrderbookRepository

logger = logging.getLogger("liqflow_api.poller")


class OrderbookPoller:
    """Polls each configured symbol on an interval and upserts snapshots."""

    def __init__(
        self,
        client: OrderBookClient,
        repo: OrderbookRepository,
        symbols: List[str],
        interval_seconds: float,
        limit: int,
    ) -> None:
        self._client = client
        self._repo = repo
        self._symbols = symbols
        self._interval = interval_seconds
        self._limit = limit

        self._task: Optional[asyncio.Task] = None
        self._stop = asyncio.Event()

        # Status surfaced via /admin/poller-status.
        self.last_poll_ts: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.poll_count: int = 0

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _poll_once(self) -> None:
        for symbol in self._symbols:
            book = await self._client.get(symbol, limit=self._limit)
            await self._repo.upsert_orderbook(
                symbol=symbol,
                last_update_id=book.get("lastUpdateId"),
                bids=book.get("bids", []),
                asks=book.get("asks", []),
            )
            try:
                stats = await self._client.get_ticker_24hr(symbol)
                await self._repo.upsert_market_stats(
                    symbol=symbol,
                    price_change=stats.get("priceChange", "0"),
                    price_change_pct=stats.get("priceChangePercent", "0"),
                    last_price=stats.get("lastPrice", "0"),
                    high_price=stats.get("highPrice", "0"),
                    low_price=stats.get("lowPrice", "0"),
                    volume=stats.get("volume", "0"),
                    quote_volume=stats.get("quoteVolume", "0"),
                )
            except Exception as exc:
                logger.warning("failed to poll ticker 24hr for %s: %s", symbol, exc)

        self.last_poll_ts = datetime.now(timezone.utc)
        self.last_error = None
        self.poll_count += 1


    async def _run(self) -> None:
        logger.info(
            "poller started: symbols=%s interval=%ss",
            self._symbols,
            self._interval,
        )
        while not self._stop.is_set():
            try:
                await self._poll_once()
            except Exception as exc:  # keep the loop alive on transient errors
                self.last_error = str(exc)
                logger.warning("poll failed: %s", exc)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=self._interval)
            except asyncio.TimeoutError:
                pass
        logger.info("poller stopped")

    def start(self) -> None:
        """Launch the loop as a background task."""
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name="orderbook-poller")

    async def stop(self) -> None:
        """Signal the loop to stop and await the task."""
        self._stop.set()
        if self._task is not None:
            try:
                await self._task
            finally:
                self._task = None

    def status(self) -> dict:
        """Serializable status for the admin endpoint."""
        return {
            "running": self.running,
            "symbols": self._symbols,
            "poll_interval_seconds": self._interval,
            "poll_count": self.poll_count,
            "last_poll_ts": (
                self.last_poll_ts.isoformat() if self.last_poll_ts else None
            ),
            "last_error": self.last_error,
        }
