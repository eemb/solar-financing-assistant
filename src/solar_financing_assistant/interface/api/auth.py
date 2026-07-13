"""API authentication and rate-limiting helpers."""

from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.dependencies import get_settings

# ---------------------------------------------------------------------------
# Rate limiter — registered on the FastAPI app in app.py
# ---------------------------------------------------------------------------


def _get_client_ip(request: Request) -> str:
    """Return the real client IP, honouring X-Forwarded-For when present.

    Behind a reverse proxy (nginx, AWS ALB, etc.) all requests arrive from
    the same internal IP; using the forwarded header gives per-client limits.

    Security note: X-Forwarded-For can be spoofed by the client if the proxy
    does not strip/overwrite it.  Configure the proxy to *overwrite*, not
    append, this header so only the value injected by the proxy is trusted.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_client_ip)

# ---------------------------------------------------------------------------
# API-key authentication
# ---------------------------------------------------------------------------

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    request: Request,  # noqa: ARG001  # explicit: shows the Request dep is in the chain
    key: str | None = Security(_api_key_header),  # noqa: B008
    settings: Settings = Depends(get_settings),  # noqa: B008
) -> None:
    """Reject requests that do not carry a valid X-API-Key header.

    Authentication is disabled when ``settings.api_key`` is ``None``
    (the default for local development).

    ``Request`` is declared explicitly so the dependency graph clearly shows
    that this function depends on the current request context.  ``settings``
    is resolved through FastAPI's DI system so that ``dependency_overrides``
    continue to work in tests.
    """
    if settings.api_key is None:
        return  # authentication disabled (local development)

    # secrets.compare_digest avoids leaking the key length/prefix via timing.
    if key is None or not secrets.compare_digest(key, settings.api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")
