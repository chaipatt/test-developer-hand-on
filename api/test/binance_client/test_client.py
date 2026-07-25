"""Unit tests for the Binance TH order-book client using a fake session."""

import pytest
from lf_tool.binance_client import BinanceClientError, OrderBookClient

_DEPTH_RESPONSE = {
    "lastUpdateId": 1027024,
    "bids": [["34.10", "5.0"], ["34.05", "2.0"]],
    "asks": [["34.20", "1.0"], ["34.25", "8.0"]],
}


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def raise_for_status(self):
        if self.status >= 400:
            import aiohttp

            raise aiohttp.ClientResponseError(
                request_info=None, history=(), status=self.status, message="boom"
            )

    async def json(self):
        return self._payload


class _FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, params))
        return self._response


@pytest.mark.asyncio
async def test_get_builds_url_and_params_and_parses():
    session = _FakeSession(_FakeResponse(_DEPTH_RESPONSE))
    client = OrderBookClient(session=session, base_url="https://api.binance.th")

    book = await client.get("USDTTHB", limit=20)

    url, params = session.calls[0]
    assert url == "https://api.binance.th/api/v1/depth"
    assert params == {"symbol": "USDTTHB", "limit": "20"}
    assert book["lastUpdateId"] == 1027024
    assert book["bids"][0] == ["34.10", "5.0"]


@pytest.mark.asyncio
async def test_get_omits_limit_when_none():
    session = _FakeSession(_FakeResponse(_DEPTH_RESPONSE))
    client = OrderBookClient(session=session)
    await client.get("USDTTHB")
    _, params = session.calls[0]
    assert params == {"symbol": "USDTTHB"}


@pytest.mark.asyncio
async def test_http_error_wrapped():
    session = _FakeSession(_FakeResponse(_DEPTH_RESPONSE, status=500))
    client = OrderBookClient(session=session)
    with pytest.raises(BinanceClientError):
        await client.get("USDTTHB")


@pytest.mark.asyncio
async def test_get_ticker_24hr():
    ticker_data = {
        "symbol": "USDTTHB",
        "priceChange": "0.10",
        "priceChangePercent": "0.300",
        "lastPrice": "33.70",
        "volume": "10000.0",
        "quoteVolume": "337000.0",
    }
    session = _FakeSession(_FakeResponse(ticker_data))
    client = OrderBookClient(session=session, base_url="https://api.binance.th")
    res = await client.get_ticker_24hr("USDTTHB")
    url, params = session.calls[0]
    assert url == "https://api.binance.th/api/v1/ticker/24hr"
    assert params == {"symbol": "USDTTHB"}
    assert res["lastPrice"] == "33.70"

