"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from solar_financing_assistant.bootstrap import build_tools
from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.auth import limiter, require_api_key
from solar_financing_assistant.interface.api.routes import router
from solar_financing_assistant.interface.api.state import AppState


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests. Please slow down."},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Accepts an optional *settings* instance so that tests and the lifespan
    share the exact same object — only one ``Settings()`` is instantiated per
    application lifecycle.
    """
    _settings = settings if settings is not None else Settings()

    # -----------------------------------------------------------------------
    # Lifespan — closure over _settings so no second instantiation is needed
    # -----------------------------------------------------------------------

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

        tools = build_tools(_settings)

        api_key = _settings.openai_api_key
        if api_key and api_key != "sk-your-key-here":
            agent: FinancingAssistantAgent | None = FinancingAssistantAgent(
                tools=tools,
                api_key=api_key,
                model=_settings.openai_model,
            )
        else:
            agent = None

        app.state.app_state = AppState(settings=_settings, tools=tools, agent=agent)
        try:
            yield
        finally:
            # Release outbound httpx clients held by the gateways.
            await tools.aclose()

    # -----------------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------------

    application = FastAPI(
        title="Solar Financing Assistant API",
        description=(
            "HTTP backend for residential solar financing simulation. Extracts energy-bill "
            "data, estimates photovoltaic projects, and computes installments using the "
            "Price method."
        ),
        version="0.1.0",
        lifespan=_lifespan,
    )

    # -----------------------------------------------------------------------
    # Middleware (order matters: outermost = first to receive the request)
    # -----------------------------------------------------------------------

    if _settings.https_redirect:
        application.add_middleware(HTTPSRedirectMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "X-Simulation-Token", "Content-Type"],
        expose_headers=["X-Simulation-Token"],
    )

    application.add_middleware(SlowAPIMiddleware)

    # -----------------------------------------------------------------------
    # Rate-limiter
    # -----------------------------------------------------------------------

    application.state.limiter = limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_handler)  # type: ignore[arg-type]

    # -----------------------------------------------------------------------
    # Router — global API-key auth applied to every route
    # -----------------------------------------------------------------------

    application.include_router(router, dependencies=[Depends(require_api_key)])

    return application


app = create_app()
