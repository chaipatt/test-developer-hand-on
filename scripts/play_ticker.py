"""Play with the new Binance TH 24hr ticker endpoint + a little quant analysis.

Fetches ``GET /api/v1/ticker/24hr`` for several TH symbols via the project's
own ``OrderBookClient`` and derives a few desk-style metrics:

* range_pct   - intraday volatility proxy: (high - low) / low
* pos_in_range- where last sits in [low, high], 0=at low .. 1=at high
* vwap        - quoteVolume / volume (24hr volume-weighted avg price)
* last_vs_vwap- last price premium/discount to VWAP (mean-reversion signal)
* quote_vol   - 24hr traded notional in the quote asset (liquidity)

Run (from api/):

    uv run python scripts/play_ticker.py
    uv run python scripts/play_ticker.py BTCTHB ETHTHB USDTTHB
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal, InvalidOperation

import aiohttp
from lf_tool.binance_client import BinanceClientError, Ticker24hr, create_client

DEFAULT_SYMBOLS = ["USDTTHB", "BTCTHB", "ETHTHB", "BNBTHB"]


def _d(value: str) -> Decimal:
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError):
        return Decimal(0)


def analyze(t: Ticker24hr) -> dict[str, object]:
    high, low, last = _d(t["highPrice"]), _d(t["lowPrice"]), _d(t["lastPrice"])
    vol, qvol = _d(t["volume"]), _d(t["quoteVolume"])

    rng = high - low
    range_pct = (rng / low * 100) if low else Decimal(0)
    pos = ((last - low) / rng) if rng else Decimal(0)
    vwap = (qvol / vol) if vol else Decimal(0)
    last_vs_vwap = ((last - vwap) / vwap * 100) if vwap else Decimal(0)

    return {
        "symbol": t["symbol"],
        "last": last,
        "chg_pct": _d(t["priceChangePercent"]),
        "range_pct": range_pct,
        "pos": pos,
        "vwap": vwap,
        "last_vs_vwap": last_vs_vwap,
        "quote_vol": qvol,
    }


def _fmt(row: dict[str, object]) -> str:
    return (
        f"{row['symbol']:<9} "
        f"{row['last']:>14,.4f} "
        f"{row['chg_pct']:>+7.2f}% "
        f"{row['range_pct']:>7.2f}% "
        f"{float(row['pos']):>6.2f} "  # type: ignore[arg-type]
        f"{row['vwap']:>14,.4f} "
        f"{row['last_vs_vwap']:>+7.2f}% "
        f"{row['quote_vol']:>18,.0f}"
    )


async def main(symbols: list[str]) -> None:
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=15)
    ) as session:
        client = create_client(session)
        header = (
            f"{'symbol':<9} {'last':>14} {'24h_chg':>8} {'range':>8} "
            f"{'pos':>6} {'vwap':>14} {'vs_vwap':>8} {'quote_vol':>18}"
        )
        print(header)
        print("-" * len(header))
        rows = []
        for sym in symbols:
            try:
                ticker = await client.get_ticker_24hr(sym)
            except BinanceClientError as exc:
                print(f"{sym:<9} ERROR: {exc}")
                continue
            row = analyze(ticker)
            rows.append(row)
            print(_fmt(row))

        if rows:
            most_liquid = max(rows, key=lambda r: r["quote_vol"])  # type: ignore[arg-type,return-value]
            most_volatile = max(rows, key=lambda r: r["range_pct"])  # type: ignore[arg-type,return-value]
            print(
                f"\nmost liquid (quote vol): {most_liquid['symbol']}   "
                f"most volatile (24h range): {most_volatile['symbol']}"
            )
            print(
                "pos≈1 = trading near 24h high; last_vs_vwap>0 = above VWAP "
                "(possible mean-reversion short bias, and vice versa)."
            )


if __name__ == "__main__":
    args = sys.argv[1:] or DEFAULT_SYMBOLS
    asyncio.run(main(args))
