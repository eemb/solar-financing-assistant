"""API authentication and rate-limiting helpers."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.dependencies import get_settings

# ---------------------------------------------------------------------------
# Rate limiter — registered on the FastAPI app in app.py
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# API-key authentication
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    key: str | None = Security(_api_key_header),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Reject requests that do not carry a valid X-API-Key header.

    Authentication is disabled when ``settings.api_key`` is ``None``
    (the default for local development).
    """
    if settings.api_key is not None and key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
