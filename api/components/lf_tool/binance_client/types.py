"""Response types for the Binance TH public order-book client."""

from __future__ import annotations

from typing import List, TypedDict


class Orderbook(TypedDict):
    """Shape of ``GET /api/v1/depth``.

    ``bids`` / ``asks`` are arrays of ``[price, quantity]`` pairs where both
    elements are strings (the exchange returns them verbatim).
    """

    lastUpdateId: int
    bids: List[List[str]]
    asks: List[List[str]]


class Ticker24hr(TypedDict):
    """Shape of ``GET /api/v1/ticker/24hr``."""

    symbol: str
    priceChange: str
    priceChangePercent: str
    weightedAvgPrice: str
    prevClosePrice: str
    lastPrice: str
    lastQty: str
    bidPrice: str
    bidQty: str
    askPrice: str
    askQty: str
    openPrice: str
    highPrice: str
    lowPrice: str
    volume: str
    quoteVolume: str
    openTime: int
    closeTime: int
    firstId: int
    lastId: int
    count: int

