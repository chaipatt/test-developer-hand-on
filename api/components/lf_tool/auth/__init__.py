"""Authentication + RBAC."""

from lf_tool.auth.core import (
    AuthError,
    Principal,
    create_access_token,
    decode_access_token,
    permissions_for,
    verify_password,
)
from lf_tool.auth.deps import (
    get_current_principal,
    require_admin,
    require_user,
)

__all__ = [
    "AuthError",
    "Principal",
    "create_access_token",
    "decode_access_token",
    "get_current_principal",
    "permissions_for",
    "require_admin",
    "require_user",
    "verify_password",
]
