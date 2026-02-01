"""JARVIS API - Authentication utilities."""

import os
from typing import Optional

from fastapi import Header, HTTPException, status


# Load API secret from environment
API_SECRET = os.getenv("JARVIS_API_SECRET")


async def verify_token(authorization: Optional[str] = Header(None)) -> None:
    """Verify Bearer token for protected endpoints.

    If JARVIS_API_SECRET is not set, authentication is disabled (local dev mode).

    Args:
        authorization: Authorization header value

    Raises:
        HTTPException: If authentication fails
    """
    # If no secret configured, skip auth (local dev mode)
    if not API_SECRET:
        return

    # Require auth header
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Validate Bearer token format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract and validate token
    token = authorization.split(" ", 1)[1]
    if token != API_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return bool(API_SECRET)
