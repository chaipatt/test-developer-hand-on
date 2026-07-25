"""API-level tests with a fake repo (no DB / no network).

TestClient is used without its context manager, so the FastAPI lifespan does
not run; we inject fakes onto ``app.state`` directly.
"""

from datetime import datetime, timezone
from types import SimpleNamespace

import bcrypt
import pytest
from fastapi.testclient import TestClient
from lf_tool.liqflow_api.config import LiqflowApiConfig
from lf_tool.liqflow_api.core import app
from lf_tool.orderbook_repo import MarketStats, OrderbookSnapshot, User

PASSWORD = "secret-pw"
_HASH = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt(rounds=4)).decode()


def _user(email, role, is_active=True):
    now = datetime.now(timezone.utc)
    return User(
        id=1,
        email=email,
        password_hash=_HASH,
        role=role,
        is_active=is_active,
        description=f"{role} demo account",
        created_at=now,
        updated_at=now,
    )


class FakeRepo:
    def __init__(self):
        self.users = {
            "user@liqflow.test": _user("user@liqflow.test", "user"),
            "admin@liqflow.test": _user("admin@liqflow.test", "admin"),
            "unauthorized@liqflow.test": _user(
                "unauthorized@liqflow.test", "user", is_active=False
            ),
        }
        now = datetime.now(timezone.utc)
        self.snapshot = OrderbookSnapshot(
            id=1,
            symbol="USDTTHB",
            last_update_id=42,
            bids=[["34.10", "5.0"], ["34.05", "2.0"]],
            asks=[["34.20", "1.0"], ["34.25", "8.0"]],
            ts=now,
            updated_at=now,
        )
        self.market_stats = MarketStats(
            symbol="USDTTHB",
            price_change="0.10",
            price_change_pct="0.30",
            last_price="34.15",
            high_price="34.30",
            low_price="34.00",
            volume="10000.0",
            quote_volume="341500.0",
            ts=now,
            updated_at=now,
        )

    async def get_user_by_email(self, email):
        return self.users.get(email)

    async def list_users(self):
        return list(self.users.values())

    async def get_latest_orderbook(self, symbol):
        return self.snapshot if symbol == "USDTTHB" else None

    async def get_latest_market_stats(self, symbol):
        return self.market_stats if symbol == "USDTTHB" else None


class FakePoller:
    def status(self):
        return {"running": True, "symbols": ["USDTTHB"], "poll_count": 3}


@pytest.fixture()
def client():
    app.state.config = LiqflowApiConfig(jwt_secret="test-secret")
    app.state.repo = FakeRepo()
    app.state.poller = FakePoller()
    return TestClient(app)


def _login(client, email):
    return client.post("/auth/login", json={"email": email, "password": PASSWORD})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_public_orderbook_no_auth(client):
    resp = client.get("/orderbook/USDTTHB")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "USDTTHB"
    assert body["best_bid"] == ["34.10", "5.0"]
    assert body["best_ask"] == ["34.20", "1.0"]
    # spread = 34.20 - 34.10
    assert body["spread"].startswith("0.1")


def test_market_stats_endpoint(client):
    resp = client.get("/market-stats/USDTTHB")
    assert resp.status_code == 200
    body = resp.json()
    assert body["symbol"] == "USDTTHB"
    assert body["last_price"] == "34.15"
    assert body["high_price"] == "34.30"


def test_login_rejects_inactive_user(client):
    resp = _login(client, "unauthorized@liqflow.test")
    assert resp.status_code == 401


def test_login_rejects_wrong_password(client):
    resp = client.post(
        "/auth/login", json={"email": "user@liqflow.test", "password": "nope"}
    )
    assert resp.status_code == 401


def test_me_returns_role_and_permissions(client):
    token = _login(client, "user@liqflow.test").json()["access_token"]
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = resp.json()
    assert body["role"] == "user"
    assert body["description"]
    assert "orderbook:full" in body["permissions"]
    assert "admin:users" not in body["permissions"]


def test_full_book_requires_auth(client):
    assert client.get("/orderbook/USDTTHB/full").status_code == 401


def test_user_cannot_reach_admin(client):
    token = _login(client, "user@liqflow.test").json()["access_token"]
    resp = client.get("/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_exchange_compare_requires_admin(client):
    # unauthenticated -> 401
    assert client.get("/admin/exchange-compare").status_code == 401
    # user role -> 403
    token = _login(client, "user@liqflow.test").json()["access_token"]
    resp = client.get(
        "/admin/exchange-compare", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_exchange_compare_admin_ok(client, monkeypatch):
    from lf_tool.liqflow_api import core
    from lf_tool.liqflow_api.core import ExchangeComparison, ExchangeQuote

    async def _fake_build(session, binance_base_url):
        return [
            ExchangeComparison(
                symbol="USDT/THB",
                binance=ExchangeQuote(
                    exchange="Binance TH", last_price="33.66", best_bid="33.65"
                ),
                bitkub=ExchangeQuote(
                    exchange="Bitkub", last_price="33.64", best_bid="33.63"
                ),
                arbitrage_spread_pct="-0.059",
            )
        ]

    monkeypatch.setattr(core, "build_exchange_comparison", _fake_build)
    # Endpoint reads app.state.deps.session before delegating to the (patched)
    # builder; a stub is enough since the builder ignores it here.
    app.state.deps = SimpleNamespace(session=None)
    token = _login(client, "admin@liqflow.test").json()["access_token"]
    resp = client.get(
        "/admin/exchange-compare", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["pairs"][0]["symbol"] == "USDT/THB"
    assert body["pairs"][0]["binance"]["last_price"] == "33.66"
    assert body["pairs"][0]["arbitrage_spread_pct"] == "-0.059"


def test_admin_can_list_users_and_poller(client):
    token = _login(client, "admin@liqflow.test").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    users = client.get("/admin/users", headers=headers)
    assert users.status_code == 200
    assert len(users.json()) == 3
    status = client.get("/admin/poller-status", headers=headers)
    assert status.status_code == 200
    assert status.json()["running"] is True
