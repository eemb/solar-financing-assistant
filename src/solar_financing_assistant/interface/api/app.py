"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from solar_financing_assistant.bootstrap import build_tools
from solar_financing_assistant.config.settings import Settings
from solar_financing_assistant.interface.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Build all application-scoped singletons once and store them on app.state.

    Using app.state instead of module-level lru_cache means:
    - Each FastAPI instance (including TestClient instances) owns its own state.
    - No cross-test state leakage through a shared InMemorySimulationRepository.
    - FinancingAssistantAgent (and its OpenAI HTTP client) is created once, not
      per-request.
    """
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

    app.state.settings = settings
    app.state.tools = tools
    app.state.agent = agent

    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
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
    application.include_router(router)
    return application


app = create_app()
