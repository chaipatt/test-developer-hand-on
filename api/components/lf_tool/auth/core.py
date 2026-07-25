"""Auth logic: password verification, JWT issue/decode, RBAC permissions.

Framework-agnostic. The FastAPI wiring (``require_user`` / ``require_admin``)
lives in ``deps.py``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

import bcrypt
import jwt
from pydantic import BaseModel

JWT_ALGORITHM = "HS256"

# Role -> permissions the UI/BFF use to render only what the user may access.
# Admin is a strict superset of user.
_PERMISSIONS: dict[str, List[str]] = {
    "user": ["orderbook:read", "orderbook:full"],
    "admin": ["orderbook:read", "orderbook:full", "admin:users", "admin:poller"],
}


class Principal(BaseModel):
    """The authenticated caller, as returned by ``GET /auth/me``."""

    email: str
    role: str
    description: str
    permissions: List[str]


class AuthError(Exception):
    """Raised when a token is missing/invalid or a login is rejected."""


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def permissions_for(role: str) -> List[str]:
    """Return the permission list for a role (empty for unknown roles)."""
    return list(_PERMISSIONS.get(role, []))


def create_access_token(
    email: str, role: str, secret: str, expires_minutes: int = 720
) -> str:
    """Mint a signed HS256 JWT for a verified user."""
    now = datetime.now(timezone.utc)
    claims = {
        "sub": email,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, secret: str) -> dict:
    """Decode and verify a JWT, returning its claims. Raises on failure."""
    try:
        return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise AuthError(f"invalid token: {exc}") from exc
