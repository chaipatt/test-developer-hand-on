"""Tiny public client for the Binance TH order-book depth endpoint.

Cousin of the real ``xclient_binance_th`` component: an ``attrs`` class over an
injected ``aiohttp.ClientSession`` (the client never owns/closes the session).
Only the public, unauthenticated ``GET /api/v1/depth`` endpoint is implemented.
"""

from __future__ import annotations

import asyncio
from typing import Optional

import aiohttp
from attrs import define, field
from lf_tool.binance_client.types import Orderbook, Ticker24hr

DEFAULT_BASE_URL = "https://api.binance.th"
DEPTH_ENDPOINT = "/api/v1/depth"
TICKER_24HR_ENDPOINT = "/api/v1/ticker/24hr"


class BinanceClientError(Exception):
    """Raised when a Binance TH request fails."""

    def __init__(self, url: str, status: Optional[int], body: object) -> None:
        super().__init__(f"Binance TH error {status} on {url}: {body!r}")
        self.url = url
        self.status = status
        self.body = body


@define(slots=True, kw_only=True)
class OrderBookClient:
    """Fetch order-book depth and market data from the Binance TH public REST API."""

    session: aiohttp.ClientSession
    base_url: str = field(default=DEFAULT_BASE_URL)

    async def get(self, symbol: str, limit: Optional[int] = None) -> Orderbook:
        """Return the order book for ``symbol`` (e.g. ``USDTTHB``).

        ``limit`` is the depth (default 500, max 1000 on the exchange side).
        """
        url = f"{self.base_url}{DEPTH_ENDPOINT}"
        params: dict[str, str] = {"symbol": symbol}
        if limit is not None:
            params["limit"] = str(limit)
        try:
            async with self.session.get(url, params=params) as resp:
                resp.raise_for_status()
                data: Orderbook = await resp.json()
                return data
        except aiohttp.ClientResponseError as exc:
            raise BinanceClientError(url, exc.status, exc.message) from exc
        except asyncio.TimeoutError as exc:
            raise BinanceClientError(url, None, f"timeout: {exc}") from exc
        except aiohttp.ClientError as exc:
            raise BinanceClientError(url, None, str(exc)) from exc

    async def get_ticker_24hr(self, symbol: str) -> Ticker24hr:
        """Return 24hr price change statistics for ``symbol``."""
        url = f"{self.base_url}{TICKER_24HR_ENDPOINT}"
        params: dict[str, str] = {"symbol": symbol}
        try:
            async with self.session.get(url, params=params) as resp:
                resp.raise_for_status()
                data: Ticker24hr = await resp.json()
                return data
        except aiohttp.ClientResponseError as exc:
            raise BinanceClientError(url, exc.status, exc.message) from exc
        except asyncio.TimeoutError as exc:
            raise BinanceClientError(url, None, f"timeout: {exc}") from exc
        except aiohttp.ClientError as exc:
            raise BinanceClientError(url, None, str(exc)) from exc


def create_client(
    session: aiohttp.ClientSession,
    base_url: str = DEFAULT_BASE_URL,
) -> OrderBookClient:
    """Build an :class:`OrderBookClient` over a shared session."""
    return OrderBookClient(session=session, base_url=base_url)

