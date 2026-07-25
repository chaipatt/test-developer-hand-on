"""Cross-exchange THB ticker board: Binance TH vs Bitkub.

For each THB pair (USDT/THB, BTC/THB, ETH/THB) this script fetches, concurrently
from both exchanges, the 24hr ticker and the top of the order book, then renders
one side-by-side comparison table per pair with a coloured arbitrage delta.

Data sources
------------
* Binance TH (via this project's own ``OrderBookClient``):
    - ``GET /api/v1/ticker/24hr``  -> last, 24h change %, quote volume
    - ``GET /api/v1/depth``        -> best bid / best ask
* Bitkub public REST (raw ``aiohttp``):
    - ``GET /api/market/ticker``   -> last, 24h change %, quote volume
    - ``GET /api/market/books``    -> best bid / best ask

All money math uses ``Decimal`` (values coerced through ``str`` first) to avoid
binary-float rounding. Network + JSON parsing is wrapped per exchange so one
side failing never crashes the board.

Run (from api/)::

    uv run python scripts/play_ticker.py
    uv run python scripts/play_ticker.py USDTTHB BTCTHB
"""

from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

import aiohttp
from lf_tool.binance_client import BinanceClientError, create_client
from rich.console import Console
from rich.table import Table

BITKUB_BASE_URL = "https://api.bitkub.com"
BITKUB_TICKER_ENDPOINT = "/api/market/ticker"
BITKUB_BOOKS_ENDPOINT = "/api/market/books"

# Binance TH symbol (no separator) -> human label + Bitkub symbol (THB_<base>).
DEFAULT_SYMBOLS = ["USDTTHB", "BTCTHB", "ETHTHB"]


def _label(binance_symbol: str) -> str:
    """``USDTTHB`` -> ``USDT/THB`` (assumes a THB quote)."""
    if binance_symbol.upper().endswith("THB"):
        base = binance_symbol[:-3]
        return f"{base.upper()}/THB"
    return binance_symbol.upper()


def _bitkub_symbol(binance_symbol: str) -> str:
    """``USDTTHB`` -> ``THB_USDT`` (Bitkub quotes base against THB, reversed)."""
    base = (
        binance_symbol[:-3]
        if binance_symbol.upper().endswith("THB")
        else binance_symbol
    )
    return f"THB_{base.upper()}"


def _d(value: object) -> Optional[Decimal]:
    """Best-effort Decimal via ``str`` (handles both string and numeric JSON)."""
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


@dataclass(slots=True)
class Quote:
    """One exchange's view of one pair. ``error`` set means the fetch failed."""

    exchange: str
    last: Optional[Decimal] = None
    chg_pct: Optional[Decimal] = None
    quote_vol: Optional[Decimal] = None
    best_bid: Optional[Decimal] = None
    best_ask: Optional[Decimal] = None
    error: Optional[str] = None

    @property
    def spread_pct(self) -> Optional[Decimal]:
        if self.best_bid and self.best_ask and self.best_bid > 0:
            return (self.best_ask - self.best_bid) / self.best_bid * 100
        return None


async def fetch_binance(session: aiohttp.ClientSession, symbol: str) -> Quote:
    """Binance TH 24hr ticker + depth top-of-book, via the project client."""
    client = create_client(session)
    try:
        ticker, book = await asyncio.gather(
            client.get_ticker_24hr(symbol),
            client.get(symbol, limit=5),
        )
    except BinanceClientError as exc:
        return Quote(exchange="Binance TH", error=str(exc))

    bids, asks = book.get("bids") or [], book.get("asks") or []
    return Quote(
        exchange="Binance TH",
        last=_d(ticker.get("lastPrice")),
        chg_pct=_d(ticker.get("priceChangePercent")),
        quote_vol=_d(ticker.get("quoteVolume")),
        best_bid=_d(bids[0][0]) if bids else None,
        best_ask=_d(asks[0][0]) if asks else None,
    )


async def fetch_bitkub(session: aiohttp.ClientSession, symbol: str) -> Quote:
    """Bitkub public ticker + books top-of-book."""
    sym = _bitkub_symbol(symbol)
    try:
        # The ticker endpoint no longer accepts a ``sym`` filter (returns
        # error 99); fetch the whole board and index by symbol below.
        async with session.get(f"{BITKUB_BASE_URL}{BITKUB_TICKER_ENDPOINT}") as resp:
            resp.raise_for_status()
            ticker_body = await resp.json()
        async with session.get(
            f"{BITKUB_BASE_URL}{BITKUB_BOOKS_ENDPOINT}",
            params={"sym": sym, "lmt": "5"},
        ) as resp:
            resp.raise_for_status()
            books_body = await resp.json()
    except aiohttp.ClientError as exc:
        return Quote(exchange="Bitkub", error=str(exc))
    except (ValueError, TypeError) as exc:  # JSON decode / shape issues
        return Quote(exchange="Bitkub", error=f"parse error: {exc}")

    ticker = ticker_body.get(sym) if isinstance(ticker_body, dict) else None
    if not isinstance(ticker, dict):
        return Quote(exchange="Bitkub", error=f"no ticker for {sym}")

    # Bitkub's ticker carries the authoritative top-of-book (highestBid /
    # lowestAsk track `last`); the public /books endpoint can return stale
    # outer rows, so trust the ticker first and fall back to the book only
    # when the ticker omits a side. books rows: [id, ts, volume_thb, rate,
    # amount_base] with rate = price at index 3.
    result = books_body.get("result", {}) if isinstance(books_body, dict) else {}
    bids = result.get("bids") or []
    asks = result.get("asks") or []
    best_bid = _d(ticker.get("highestBid")) or (
        _d(bids[0][3]) if bids and len(bids[0]) > 3 else None
    )
    best_ask = _d(ticker.get("lowestAsk")) or (
        _d(asks[0][3]) if asks and len(asks[0]) > 3 else None
    )

    return Quote(
        exchange="Bitkub",
        last=_d(ticker.get("last")),
        chg_pct=_d(ticker.get("percentChange")),
        quote_vol=_d(ticker.get("quoteVolume")),
        best_bid=best_bid,
        best_ask=best_ask,
    )


def _num(value: Optional[Decimal], fmt: str) -> str:
    return format(value, fmt) if value is not None else "[dim]n/a[/dim]"


def _chg_cell(value: Optional[Decimal]) -> str:
    if value is None:
        return "[dim]n/a[/dim]"
    colour = "green" if value >= 0 else "red"
    return f"[{colour}]{value:+.2f}%[/{colour}]"


def _spread_cell(value: Optional[Decimal]) -> str:
    return f"{value:.3f}%" if value is not None else "[dim]n/a[/dim]"


def build_table(label: str, binance: Quote, bitkub: Quote) -> Table:
    table = Table(title=f"[bold]{label}[/bold]", title_justify="left", expand=False)
    table.add_column("Exchange", style="cyan", no_wrap=True)
    table.add_column("Last", justify="right")
    table.add_column("24h Chg", justify="right")
    table.add_column("Vol (THB)", justify="right")
    table.add_column("Best Bid", justify="right")
    table.add_column("Best Ask", justify="right")
    table.add_column("Spread", justify="right")

    for q in (binance, bitkub):
        if q.error:
            table.add_row(q.exchange, f"[red]ERR: {q.error}[/red]", "", "", "", "", "")
            continue
        table.add_row(
            q.exchange,
            _num(q.last, ",.4f"),
            _chg_cell(q.chg_pct),
            _num(q.quote_vol, ",.0f"),
            _num(q.best_bid, ",.4f"),
            _num(q.best_ask, ",.4f"),
            _spread_cell(q.spread_pct),
        )
    return table


def arbitrage_line(binance: Quote, bitkub: Quote) -> Optional[str]:
    """% delta of Bitkub last vs Binance TH last (+ = Bitkub richer)."""
    if binance.error or bitkub.error:
        return None
    if not (binance.last and bitkub.last and binance.last > 0):
        return None
    delta = (bitkub.last - binance.last) / binance.last * 100
    colour = "green" if abs(delta) >= Decimal("0.1") else "yellow"
    direction = "Bitkub above Binance" if delta > 0 else "Binance above Bitkub"
    return (
        f"  [b]Arbitrage delta[/b]: [{colour}]{delta:+.3f}%[/{colour}] "
        f"([dim]{direction}, last vs last[/dim])"
    )


async def run(symbols: list[str]) -> None:
    console = Console()
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        tasks = [
            asyncio.gather(fetch_binance(session, sym), fetch_bitkub(session, sym))
            for sym in symbols
        ]
        results = await asyncio.gather(*tasks)

    for sym, (binance, bitkub) in zip(symbols, results):
        console.print(build_table(_label(sym), binance, bitkub))
        line = arbitrage_line(binance, bitkub)
        if line:
            console.print(line)
        console.print()


if __name__ == "__main__":
    args = sys.argv[1:] or DEFAULT_SYMBOLS
    asyncio.run(run(args))
