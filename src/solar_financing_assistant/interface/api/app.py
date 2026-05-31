"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from solar_financing_assistant.bootstrap import build_tools
from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.auth import limiter, require_api_key
from solar_financing_assistant.interface.api.routes import router
from solar_financing_assistant.interface.api.state import AppState


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Build all application-scoped singletons once and store them on app.state."""
    from solar_financing_assistant.infrastructure.llm.agent import FinancingAssistantAgent

    settings = Settings()
    tools = build_tools(settings)

    api_key = settings.openai_api_key
    if api_key and api_key != "sk-your-key-here":
        agent = FinancingAssistantAgent(
            tools=tools,
            api_key=api_key,
            model=settings.openai_model,
        )
    else:
        agent = None

    app.state.app_state = AppState(settings=settings, tools=tools, agent=agent)

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    _settings = Settings()

    application = FastAPI(
        title="Solar Financing Assistant API",
        description=(
            "Backend HTTP para simulação de financiamento de energia solar residencial. "
            "Extrai dados de contas de energia, estima projetos fotovoltaicos e calcula "
            "parcelas pelo método Price."
        ),
        version="0.1.0",
        lifespan=lifespan,
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
        allow_headers=["X-API-Key", "Content-Type"],
    )

    application.add_middleware(SlowAPIMiddleware)

    # -----------------------------------------------------------------------
    # Rate-limiter state (slowapi reads this from app.state.limiter)
    # -----------------------------------------------------------------------

    application.state.limiter = limiter
    application.add_exception_handler(
        RateLimitExceeded,
        lambda req, exc: __import__("fastapi").responses.JSONResponse(  # type: ignore[arg-type]
            status_code=429,
            content={"detail": "Too many requests. Please slow down."},
        ),
    )

    # -----------------------------------------------------------------------
    # Router — global API-key auth applied to every route
    # -----------------------------------------------------------------------

    application.include_router(router, dependencies=[Depends(require_api_key)])

    return application


app = create_app()
