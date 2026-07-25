"""Tiny public client for the Bitkub market REST endpoints.

Sibling of :mod:`lf_tool.binance_client`: an ``attrs`` class over an injected
``aiohttp.ClientSession`` (the client never owns/closes the session). Only the
public, unauthenticated endpoints we need are implemented:

* ``GET /api/market/ticker`` — 24hr stats for **all** markets, keyed
  ``THB_<BASE>``. Bitkub's ticker no longer accepts a ``sym`` filter (it
  returns error 99), so we fetch the whole board and index it caller-side.
* ``GET /api/market/books`` — order-book depth for one ``THB_<BASE>`` market.
"""

from __future__ import annotations

import asyncio
from typing import Dict

import aiohttp
from attrs import define, field
from lf_tool.bitkub_client.types import BitkubBooks, BitkubTicker

DEFAULT_BASE_URL = "https://api.bitkub.com"
TICKER_ENDPOINT = "/api/market/ticker"
BOOKS_ENDPOINT = "/api/market/books"


class BitkubClientError(Exception):
    """Raised when a Bitkub request fails."""

    def __init__(self, url: str, status: object, body: object) -> None:
        super().__init__(f"Bitkub error {status} on {url}: {body!r}")
        self.url = url
        self.status = status
        self.body = body


def to_bitkub_symbol(binance_symbol: str) -> str:
    """``USDTTHB`` -> ``THB_USDT`` (Bitkub quotes the base against THB)."""
    upper = binance_symbol.upper()
    base = upper[:-3] if upper.endswith("THB") else upper
    return f"THB_{base}"


@define(slots=True, kw_only=True)
class BitkubClient:
    """Fetch 24hr ticker and order-book depth from the Bitkub public REST API."""

    session: aiohttp.ClientSession
    base_url: str = field(default=DEFAULT_BASE_URL)

    async def get_ticker(self) -> Dict[str, BitkubTicker]:
        """Return the 24hr ticker board for every market, keyed ``THB_<BASE>``."""
        url = f"{self.base_url}{TICKER_ENDPOINT}"
        try:
            async with self.session.get(url) as resp:
                resp.raise_for_status()
                data: Dict[str, BitkubTicker] = await resp.json()
                return data
        except aiohttp.ClientResponseError as exc:
            raise BitkubClientError(url, exc.status, exc.message) from exc
        except asyncio.TimeoutError as exc:
            raise BitkubClientError(url, None, f"timeout: {exc}") from exc
        except aiohttp.ClientError as exc:
            raise BitkubClientError(url, None, str(exc)) from exc

    async def get_books(self, symbol: str, limit: int = 5) -> BitkubBooks:
        """Return order-book depth for one ``THB_<BASE>`` ``symbol``."""
        url = f"{self.base_url}{BOOKS_ENDPOINT}"
        params = {"sym": symbol, "lmt": str(limit)}
        try:
            async with self.session.get(url, params=params) as resp:
                resp.raise_for_status()
                data: BitkubBooks = await resp.json()
                return data
        except aiohttp.ClientResponseError as exc:
            raise BitkubClientError(url, exc.status, exc.message) from exc
        except asyncio.TimeoutError as exc:
            raise BitkubClientError(url, None, f"timeout: {exc}") from exc
        except aiohttp.ClientError as exc:
            raise BitkubClientError(url, None, str(exc)) from exc


def create_client(
    session: aiohttp.ClientSession,
    base_url: str = DEFAULT_BASE_URL,
) -> BitkubClient:
    """Build a :class:`BitkubClient` over a shared session."""
    return BitkubClient(session=session, base_url=base_url)
