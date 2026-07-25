"""FastAPI app for liqflow_api.

Wires the asyncpg pool + poller into the lifespan, then exposes:
  - /health, /ready
  - POST /auth/login, GET /auth/me            (auth + RBAC)
  - GET /orderbook/{symbol}                    (public, top-of-book)
  - GET /orderbook/{symbol}/full               (user)
  - GET /admin/users, GET /admin/poller-status (admin)

Server-side role checks (auth deps) are authoritative; the UI only mirrors them.
"""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional

import aiohttp
from fastapi import Depends, FastAPI, HTTPException, status
from lf_tool.auth import (
    Principal,
    create_access_token,
    get_current_principal,
    require_admin,
    require_user,
    verify_password,
)
from lf_tool.binance_client import BinanceClientError
from lf_tool.binance_client import create_client as create_binance_client
from lf_tool.bitkub_client import BitkubClientError, to_bitkub_symbol
from lf_tool.bitkub_client import create_client as create_bitkub_client
from lf_tool.liqflow_api.config import LiqflowApiConfig, config
from lf_tool.liqflow_api.deps import build_deps, close_deps
from lf_tool.orderbook_repo import OrderbookSnapshot
from pydantic import BaseModel

logger = logging.getLogger("liqflow_api")


# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #
class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class TopOfBook(BaseModel):
    symbol: str
    ts: str
    last_update_id: Optional[int]
    best_bid: Optional[List[str]]
    best_ask: Optional[List[str]]
    spread: Optional[str]
    bids: List[List[str]]  # top few levels, for a public preview
    asks: List[List[str]]


class FullBook(BaseModel):
    symbol: str
    ts: str
    last_update_id: Optional[int]
    bids: List[List[str]]
    asks: List[List[str]]


class AdminUser(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    description: str
    created_at: str


_PUBLIC_PREVIEW_LEVELS = 5


# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.config = config
    deps = await build_deps(config)
    app.state.deps = deps
    app.state.repo = deps.repo
    app.state.poller = deps.poller
    deps.poller.start()
    logger.info("liqflow_api started")
    try:
        yield
    finally:
        await close_deps(deps)
        logger.info("liqflow_api stopped")


app = FastAPI(title="liqflow_api", version="0.1.0", lifespan=lifespan)


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    pool = app.state.deps.pool
    try:
        async with pool.acquire(timeout=5.0) as conn:
            await conn.fetchval("SELECT 1;")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database not ready: {exc}",
        ) from exc
    return {"status": "ready"}


# --------------------------------------------------------------------------- #
# Auth + RBAC
# --------------------------------------------------------------------------- #
@app.post("/auth/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    cfg: LiqflowApiConfig = app.state.config
    user = await app.state.repo.get_user_by_email(body.email)
    if (
        user is None
        or not user.is_active
        or not verify_password(body.password, user.password_hash)
    ):
        # Same response for unknown / disabled / wrong password (no user enum).
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials or inactive account",
        )
    token = create_access_token(
        user.email, user.role, cfg.jwt_secret, cfg.jwt_expires_minutes
    )
    return LoginResponse(access_token=token, role=user.role)


@app.get("/auth/me", response_model=Principal)
async def me(principal: Principal = Depends(get_current_principal)) -> Principal:
    return principal


# --------------------------------------------------------------------------- #
# Order book
# --------------------------------------------------------------------------- #
async def _latest_or_404(symbol: str) -> OrderbookSnapshot:
    snap = await app.state.repo.get_latest_orderbook(symbol)
    if snap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no order-book snapshot yet for {symbol}",
        )
    return snap


@app.get("/orderbook/{symbol}", response_model=TopOfBook)
async def orderbook_top(symbol: str) -> TopOfBook:
    """Public: best bid/ask + a short preview of the book."""
    snap = await _latest_or_404(symbol.upper())
    best_bid = snap.bids[0] if snap.bids else None
    best_ask = snap.asks[0] if snap.asks else None
    spread = None
    if best_bid and best_ask:
        spread = f"{float(best_ask[0]) - float(best_bid[0]):.8f}"
    return TopOfBook(
        symbol=snap.symbol,
        ts=snap.ts.isoformat(),
        last_update_id=snap.last_update_id,
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        bids=snap.bids[:_PUBLIC_PREVIEW_LEVELS],
        asks=snap.asks[:_PUBLIC_PREVIEW_LEVELS],
    )


class MarketStatsResponse(BaseModel):
    symbol: str
    price_change: str
    price_change_pct: str
    last_price: str
    high_price: str
    low_price: str
    volume: str
    quote_volume: str
    ts: str


@app.get("/market-stats/{symbol}", response_model=MarketStatsResponse)
async def market_stats(symbol: str) -> MarketStatsResponse:
    """Public: 24hr price change and volume statistics."""
    stats = await app.state.repo.get_latest_market_stats(symbol.upper())
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no market stats snapshot yet for {symbol}",
        )
    return MarketStatsResponse(
        symbol=stats.symbol,
        price_change=stats.price_change,
        price_change_pct=stats.price_change_pct,
        last_price=stats.last_price,
        high_price=stats.high_price,
        low_price=stats.low_price,
        volume=stats.volume,
        quote_volume=stats.quote_volume,
        ts=stats.ts.isoformat(),
    )


@app.get("/orderbook/{symbol}/full", response_model=FullBook)
async def orderbook_full(symbol: str, _: Principal = Depends(require_user)) -> FullBook:
    """User: the full stored depth."""
    snap = await _latest_or_404(symbol.upper())
    return FullBook(
        symbol=snap.symbol,
        ts=snap.ts.isoformat(),
        last_update_id=snap.last_update_id,
        bids=snap.bids,
        asks=snap.asks,
    )


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
@app.get("/admin/users", response_model=List[AdminUser])
async def admin_users(_: Principal = Depends(require_admin)) -> List[AdminUser]:
    users = await app.state.repo.list_users()
    return [
        AdminUser(
            id=u.id,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            description=u.description,
            created_at=u.created_at.isoformat(),
        )
        for u in users
    ]


@app.get("/admin/poller-status")
async def admin_poller_status(_: Principal = Depends(require_admin)) -> dict:
    return app.state.poller.status()


# --------------------------------------------------------------------------- #
# Admin: cross-exchange comparison (Binance TH vs Bitkub)
# --------------------------------------------------------------------------- #
# (binance symbol, human label). The Bitkub symbol is derived via
# ``to_bitkub_symbol`` (USDTTHB -> THB_USDT).
_COMPARE_SYMBOLS: List[tuple[str, str]] = [
    ("USDTTHB", "USDT/THB"),
    ("BTCTHB", "BTC/THB"),
    ("ETHTHB", "ETH/THB"),
]


class ExchangeQuote(BaseModel):
    """One exchange's live view of a pair. ``error`` set means the fetch failed.

    All numeric fields are strings to preserve exact precision (no float
    rounding); ``None`` when unavailable.
    """

    exchange: str
    last_price: Optional[str] = None
    price_change_pct: Optional[str] = None
    quote_volume: Optional[str] = None
    best_bid: Optional[str] = None
    best_ask: Optional[str] = None
    spread_pct: Optional[str] = None
    error: Optional[str] = None


class ExchangeComparison(BaseModel):
    symbol: str  # human label, e.g. "USDT/THB"
    binance: ExchangeQuote
    bitkub: ExchangeQuote
    # (bitkub.last - binance.last) / binance.last * 100; + = Bitkub richer.
    arbitrage_spread_pct: Optional[str] = None


class ExchangeCompareResponse(BaseModel):
    generated_at: str
    pairs: List[ExchangeComparison]


def _dec(value: object) -> Optional[Decimal]:
    """Best-effort Decimal via ``str`` (handles string and numeric JSON)."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _fmt(value: Optional[Decimal], places: str = "0.00000001") -> Optional[str]:
    if value is None:
        return None
    # Fixed-point (never scientific), then trim trailing zeros: 62530.00 -> 62530.
    text = format(value.quantize(Decimal(places)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _spread_pct(bid: Optional[Decimal], ask: Optional[Decimal]) -> Optional[Decimal]:
    if bid is not None and ask is not None and bid > 0:
        return (ask - bid) / bid * 100
    return None


async def _binance_quote(client, symbol: str) -> ExchangeQuote:
    try:
        ticker, book = await asyncio.gather(
            client.get_ticker_24hr(symbol),
            client.get(symbol, limit=5),
        )
    except BinanceClientError as exc:
        return ExchangeQuote(exchange="Binance TH", error=str(exc))

    bids = book.get("bids") or []
    asks = book.get("asks") or []
    best_bid = _dec(bids[0][0]) if bids else None
    best_ask = _dec(asks[0][0]) if asks else None
    return ExchangeQuote(
        exchange="Binance TH",
        last_price=_fmt(_dec(ticker.get("lastPrice"))),
        price_change_pct=_fmt(_dec(ticker.get("priceChangePercent")), "0.01"),
        quote_volume=_fmt(_dec(ticker.get("quoteVolume")), "1"),
        best_bid=_fmt(best_bid),
        best_ask=_fmt(best_ask),
        spread_pct=_fmt(_spread_pct(best_bid, best_ask), "0.001"),
    )


async def _bitkub_quote(client, binance_symbol: str) -> ExchangeQuote:
    sym = to_bitkub_symbol(binance_symbol)
    try:
        ticker_board, books = await asyncio.gather(
            client.get_ticker(),
            client.get_books(sym, limit=5),
        )
    except BitkubClientError as exc:
        return ExchangeQuote(exchange="Bitkub", error=str(exc))

    ticker = ticker_board.get(sym) if isinstance(ticker_board, dict) else None
    if not isinstance(ticker, dict):
        return ExchangeQuote(exchange="Bitkub", error=f"no ticker for {sym}")

    # Bitkub's ticker carries the authoritative top-of-book (highestBid /
    # lowestAsk track `last`); the public /books outer rows can be stale, so
    # trust the ticker first and fall back to the book rate (index 3) only when
    # the ticker omits a side.
    result = books.get("result", {}) if isinstance(books, dict) else {}
    bids = result.get("bids") or []
    asks = result.get("asks") or []
    t_bid = _dec(ticker.get("highestBid"))
    t_ask = _dec(ticker.get("lowestAsk"))
    best_bid = t_bid if t_bid is not None else (
        _dec(bids[0][3]) if bids and len(bids[0]) > 3 else None
    )
    best_ask = t_ask if t_ask is not None else (
        _dec(asks[0][3]) if asks and len(asks[0]) > 3 else None
    )
    return ExchangeQuote(
        exchange="Bitkub",
        last_price=_fmt(_dec(ticker.get("last"))),
        price_change_pct=_fmt(_dec(ticker.get("percentChange")), "0.01"),
        quote_volume=_fmt(_dec(ticker.get("quoteVolume")), "1"),
        best_bid=_fmt(best_bid),
        best_ask=_fmt(best_ask),
        spread_pct=_fmt(_spread_pct(best_bid, best_ask), "0.001"),
    )


def _arbitrage_pct(binance: ExchangeQuote, bitkub: ExchangeQuote) -> Optional[str]:
    b = _dec(binance.last_price)
    k = _dec(bitkub.last_price)
    if b is not None and k is not None and b > 0:
        return _fmt((k - b) / b * 100, "0.001")
    return None


async def build_exchange_comparison(
    session: aiohttp.ClientSession, binance_base_url: str
) -> List[ExchangeComparison]:
    """Fetch both exchanges concurrently for every pair and compute metrics.

    Each exchange fetch is isolated (its client wraps failures) so one side or
    one pair failing degrades to an ``error`` row rather than a 500.
    """
    binance = create_binance_client(session, base_url=binance_base_url)
    bitkub = create_bitkub_client(session)

    async def one(binance_symbol: str, label: str) -> ExchangeComparison:
        b_quote, k_quote = await asyncio.gather(
            _binance_quote(binance, binance_symbol),
            _bitkub_quote(bitkub, binance_symbol),
        )
        return ExchangeComparison(
            symbol=label,
            binance=b_quote,
            bitkub=k_quote,
            arbitrage_spread_pct=_arbitrage_pct(b_quote, k_quote),
        )

    pairs = await asyncio.gather(*(one(sym, label) for sym, label in _COMPARE_SYMBOLS))
    return list(pairs)


@app.get("/admin/exchange-compare", response_model=ExchangeCompareResponse)
async def admin_exchange_compare(
    _: Principal = Depends(require_admin),
) -> ExchangeCompareResponse:
    """Admin: live Binance TH vs Bitkub comparison for the tracked THB pairs."""
    cfg: LiqflowApiConfig = app.state.config
    session = app.state.deps.session
    pairs = await build_exchange_comparison(session, cfg.binance_base_url)
    return ExchangeCompareResponse(
        generated_at=datetime.now(timezone.utc).isoformat(),
        pairs=pairs,
    )


# --------------------------------------------------------------------------- #
# Entrypoint
# --------------------------------------------------------------------------- #
def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    host = os.environ.get("LIQFLOW_API_HOST", "0.0.0.0")
    port = int(os.environ.get("LIQFLOW_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
