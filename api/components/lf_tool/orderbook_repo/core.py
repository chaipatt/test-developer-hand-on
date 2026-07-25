"""Repository interface (Protocol). Postgres impl lives in ``postgres.py``."""

from __future__ import annotations

from typing import List, Optional, Protocol

from lf_tool.orderbook_repo.types import MarketStats, OrderbookSnapshot, User


class OrderbookRepository(Protocol):
    """Persistence boundary for order-book snapshots, market stats, and users.

    Every method is backed by a Postgres stored function; callers depend on
    this Protocol, never on the concrete implementation.
    """

    async def upsert_orderbook(
        self,
        symbol: str,
        last_update_id: Optional[int],
        bids: List[List[str]],
        asks: List[List[str]],
    ) -> OrderbookSnapshot:
        """Overwrite the latest snapshot for ``symbol`` and return it."""
        ...

    async def get_latest_orderbook(self, symbol: str) -> Optional[OrderbookSnapshot]:
        """Return the latest snapshot for ``symbol`` (or ``None``)."""
        ...

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
        """Overwrite the latest 24hr market stats for ``symbol`` and return it."""
        ...

    async def get_latest_market_stats(self, symbol: str) -> Optional[MarketStats]:
        """Return the latest 24hr market stats for ``symbol`` (or ``None``)."""
        ...

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Return the user with ``email`` (or ``None``)."""
        ...

    async def list_users(self) -> List[User]:
        """Return all users."""
        ...

