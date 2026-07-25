"""Pydantic models for the order-book + user repositories."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

# A single [price, quantity] level as returned by the exchange (strings).
Level = List[str]


class OrderbookSnapshot(BaseModel):
    """A stored order-book snapshot for one symbol."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    last_update_id: Optional[int] = None
    bids: List[Level]
    asks: List[Level]
    ts: datetime
    updated_at: datetime


class User(BaseModel):
    """A seeded application user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    password_hash: str
    role: str
    is_active: bool
    description: str
    created_at: datetime
    updated_at: datetime


class MarketStats(BaseModel):
    """A stored 24hr market stats snapshot for one symbol."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    price_change: str
    price_change_pct: str
    last_price: str
    high_price: str
    low_price: str
    volume: str
    quote_volume: str
    ts: datetime
    updated_at: datetime

