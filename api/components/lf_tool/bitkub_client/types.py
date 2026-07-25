"""Response types for the Bitkub public market client."""

from __future__ import annotations

from typing import List, TypedDict


class BitkubTicker(TypedDict, total=False):
    """One market entry from ``GET /api/market/ticker``.

    The endpoint returns a mapping of ``THB_<BASE>`` -> this object. Numeric
    fields come back as JSON numbers (not strings), so callers coerce through
    ``str`` before ``Decimal`` to keep exact precision.
    """

    id: int
    last: float
    lowestAsk: float
    highestBid: float
    percentChange: float
    baseVolume: float
    quoteVolume: float
    high24hr: float
    low24hr: float
    change: float
    prevClose: float
    prevOpen: float
    isFrozen: int


class BitkubBooks(TypedDict, total=False):
    """Shape of ``GET /api/market/books``.

    ``result.bids`` / ``result.asks`` are arrays of
    ``[order_id, timestamp, volume_thb, rate, amount_base]`` where ``rate``
    (index 3) is the price level.
    """

    error: int
    result: "BitkubBooksResult"


class BitkubBooksResult(TypedDict, total=False):
    bids: List[list]
    asks: List[list]
