"""FastAPI auth dependencies: resolve the caller and enforce roles.

The Python API is the authoritative RBAC boundary — UI gating is cosmetic on
top of these checks. Dependencies read the repo + config from ``app.state``.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status
from lf_tool.auth.core import (
    AuthError,
    Principal,
    decode_access_token,
    permissions_for,
)


async def get_current_principal(
    request: Request,
    authorization: str | None = Header(default=None),
) -> Principal:
    """Resolve the caller from a ``Bearer`` token, or 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
        )
    token = authorization.split(" ", 1)[1].strip()

    config = request.app.state.config
    repo = request.app.state.repo
    try:
        claims = decode_access_token(token, config.jwt_secret)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    email = claims.get("sub")
    user = await repo.get_user_by_email(email) if email else None
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive or unknown user"
        )

    return Principal(
        email=user.email,
        role=user.role,
        description=user.description,
        permissions=permissions_for(user.role),
    )


async def require_user(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    """Allow any authenticated user (``user`` or ``admin``)."""
    if principal.role not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="permission denied"
        )
    return principal


async def require_admin(
    principal: Principal = Depends(get_current_principal),
) -> Principal:
    """Allow admins only."""
    if principal.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="permission denied"
        )
    return principal
