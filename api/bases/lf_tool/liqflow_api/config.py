"""Application configuration (pydantic-settings, env prefix ``LIQFLOW_API_``)."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LiqflowApiConfig(BaseSettings):
    """Settings for the liqflow_api service.

    All values are read from the environment with the ``LIQFLOW_API_`` prefix,
    e.g. ``LIQFLOW_API_POSTGRES_DSN``. See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_prefix="LIQFLOW_API_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_dsn: str = Field(
        default="postgresql://liqflow:liqflow@localhost:5432/liqflow",
        description="asyncpg-compatible Postgres DSN.",
    )
    pg_min_connections: int = 1
    pg_max_connections: int = 10

    binance_base_url: str = "https://api.binance.th"
    poll_interval_seconds: float = 5.0
    orderbook_limit: int = 20

    # Outbound HTTP timeouts (seconds) for exchange calls. Without these a hung
    # upstream (Binance/Bitkub) would tie up workers indefinitely — the admin
    # exchange-compare endpoint is polled every 5s, so an unbounded call is a
    # resource-exhaustion vector.
    http_total_timeout_seconds: float = 10.0
    http_connect_timeout_seconds: float = 5.0

    # A candidate can add more pairs here, but Liqflow only uses USDTTHB on the
    # Binance TH API today. Kept as a list so extending it is trivial.
    symbols: list[str] = Field(default_factory=lambda: ["USDTTHB"])

    jwt_secret: str = Field(
        default="dev-only-insecure-secret-change-me",
        description="HS256 signing secret for auth tokens (override in real use).",
    )
    jwt_expires_minutes: int = 720


config = LiqflowApiConfig()
