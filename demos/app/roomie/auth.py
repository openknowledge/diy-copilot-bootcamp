"""Authentication via API keys.

Clients authenticate by sending their personal API key in the
``X-Roomie-Key`` header (see ADR-0002). We deliberately do not use the
``Authorization`` header, because the corporate proxy strips it for
internal services.
"""

from fastapi import Depends, Header

from roomie.config import API_KEY_HEADER, API_KEYS
from roomie.errors import AuthenticationError, PermissionDeniedError
from roomie.models import Role, User


def get_current_user(
    api_key: str | None = Header(default=None, alias=API_KEY_HEADER),
) -> User:
    """FastAPI dependency that resolves the API key to a user.

    Raises
    ------
    AuthenticationError
        If the header is missing or the key is unknown.
    """
    if not api_key:
        raise AuthenticationError(f"Missing {API_KEY_HEADER} header.")
    entry = API_KEYS.get(api_key)
    if entry is None:
        raise AuthenticationError("Unknown API key.")
    return User(user_id=entry["user_id"], role=Role(entry["role"]))


def require_admin(user: User = Depends(get_current_user)) -> User:
    """FastAPI dependency that only lets facility admins pass."""
    if not user.is_admin:
        raise PermissionDeniedError("This action requires the facility_admin role.")
    return user
